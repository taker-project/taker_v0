/*
 * Copyright (C) 2018  Alexander Kernozhitsky <sh200105@mail.ru>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "processrunner.hpp"
#include <errno.h>
#include <fcntl.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>
#include <cmath>
#include <cstring>
#include <iostream>
#include <sstream>
#include "utils.hpp"

namespace UnixRunner {

RunnerError::RunnerError(const std::string &comment)
    : std::runtime_error(comment) {}

RunnerValidateError::RunnerValidateError(const std::string &comment)
    : RunnerError(comment) {}

#define VALIDATE_ASSERT(cond) \
  if (!(cond)) throw RunnerValidateError("assertion failed: " #cond);

void ProcessRunner::Parameters::validate() {
  VALIDATE_ASSERT(timeLimit > 0);
  VALIDATE_ASSERT(idleLimit > 0);
  VALIDATE_ASSERT(memoryLimit > 0);
  VALIDATE_ASSERT(fileIsExecutable(executable));
  VALIDATE_ASSERT(workingDir.empty() || directoryIsGood(workingDir));
  VALIDATE_ASSERT(stdinRedir.empty() || fileIsReadable(stdinRedir));
}

#undef VALIDATE_ASSERT

void ProcessRunner::Parameters::loadFromJson(const Json::Value &value) {
  using Json::Value;
  timeLimit = value.get("time-limit", Value(timeLimit)).asDouble();
  idleLimit = value.get("idle-limit", Value(timeLimit * 3.5)).asDouble();
  memoryLimit = value.get("memory-limit", Value(memoryLimit)).asDouble();
  executable = value.get("executable", Value("")).asString();
  clearEnv = value.get("clear-env", Value(clearEnv)).asBool();
  if (value.isMember("env")) {
    auto envNode = value["env"];
    if (!envNode.isObject()) {
      throw std::runtime_error("env is not object");
    }
    env.clear();
    for (const std::string &name : envNode.getMemberNames()) {
      Json::Value strValue = envNode[name];
      if (strValue.isConvertibleTo(Json::stringValue)) {
        env[name] = strValue.asString();
      }
    }
  }
  if (value.isMember("args")) {
    auto argNode = value["args"];
    if (!argNode.isArray()) {
      throw std::runtime_error("args is not an array");
    }
    args.resize(argNode.size());
    for (Json::ArrayIndex i = 0; i < argNode.size(); ++i) {
      args[i] = argNode[i].asString();
    }
  } else {
    args.clear();
  }
  workingDir = value.get("working-dir", Value("")).asString();
  stdinRedir = value.get("stdin-redir", Value("")).asString();
  stdoutRedir = value.get("stdout-redir", Value("")).asString();
  stderrRedir = value.get("stderr-redir", Value("")).asString();
}

void ProcessRunner::Parameters::loadFromJsonStr(const std::string &json) {
  std::istringstream stream(json);
  Json::Value value;
  stream >> value;
  return loadFromJson(value);
}

const char *ProcessRunner::runStatusToStr(
    UnixRunner::ProcessRunner::RunStatus status) {
  static const char *RUN_STATUS_STRS[] = {
      "ok",           "time-limit",    "idle-limit",
      "memory-limit", "runtime-error", "security-error",
      "run-fail",     "running",       "none"};
  return RUN_STATUS_STRS[static_cast<int>(status)];
}

Json::Value ProcessRunner::RunResults::saveToJson() const {
  Json::Value value;
  value["time"] = time;
  value["clock-time"] = clockTime;
  value["memory"] = memory;
  value["exitcode"] = exitCode;
  value["signal"] = signal;
  value["status"] = ProcessRunner::runStatusToStr(status);
  value["comment"] = comment;
  return value;
}

std::string ProcessRunner::RunResults::saveToJsonStr() const {
  return saveToJson().toStyledString();
}

UnixRunner::ProcessRunner::Parameters &ProcessRunner::parameters() {
  return parameters_;
}

const UnixRunner::ProcessRunner::Parameters &ProcessRunner::parameters() const {
  return parameters_;
}

const UnixRunner::ProcessRunner::RunResults &ProcessRunner::results() const {
  return results_;
}

void ProcessRunner::execute() {
  if (results_.status == RunStatus::RUNNING) {
    throw std::runtime_error("process is already running");
  }
  try {
    doExecute();
  } catch (const std::exception &e) {
    results_.status = RunStatus::RUN_FAIL;
    results_.comment = getFullExceptionMessage(e);
  }
}

void ProcessRunner::doExecute() {
  parameters_.validate();
  results_.status = RunStatus::RUNNING;
  pid_t pid = fork();
  if (pid < 0) {
    throw RunnerError(strerror(errno));
  }
  if (pid == 0) {
    try {
      handleChild();
    } catch (const std::exception &e) {
      childFailure(getFullExceptionMessage(e));
    }
  }
  handleParent(pid);
}

void ProcessRunner::handleParent(pid_t child) {
  // TODO: implement
  int status;
  wait(&status);
}

void ProcessRunner::childTry(bool success, const char *errorName) {
  if (!success) {
    childFailure(errorName, errno);
  }
}

void ProcessRunner::childTry(bool success, const std::string &errorName) {
  childTry(success, errorName.c_str());
}

void ProcessRunner::handleChild() {
  int64_t integralTimeLimit = static_cast<int64_t>(ceil(parameters_.timeLimit));
  childTry(updateLimit(RLIMIT_CPU, integralTimeLimit),
           "could not set time limit");

  int64_t memLimitBytes =
      static_cast<int64_t>(ceil(parameters_.memoryLimit * 1048576));
  childTry(updateLimit(RLIMIT_AS, memLimitBytes * 2),
           "could not set memory limit");
  childTry(updateLimit(RLIMIT_DATA, memLimitBytes * 2),
           "could not set memory limit");
  childTry(updateLimit(RLIMIT_STACK, memLimitBytes * 2),
           "could not set memory limit");

  if (!parameters_.workingDir.empty()) {
    childTry(chdir(parameters_.workingDir.c_str()) == 0,
             "could not change directory");
  }

  childRedirect(STDIN_FILENO, parameters_.stdinRedir, O_RDONLY);
  childRedirect(STDOUT_FILENO, parameters_.stdoutRedir,
                O_CREAT | O_TRUNC | O_WRONLY);
  childRedirect(STDERR_FILENO, parameters_.stderrRedir,
                O_CREAT | O_TRUNC | O_WRONLY);

  if (parameters_.clearEnv) {
    childTry(clearenv() == 0, "unable to clear environment");
  }
  for (const auto &iter : parameters_.env) {
    const std::string &key = iter.first;
    const std::string &value = iter.second;
    childTry(setenv(key.c_str(), value.c_str(), true) == 0,
             "could not set environment \"" + key + "\"");
  }

  int argc = static_cast<int>(parameters_.args.size()) + 1;
  char **argv = new char *[argc];
  argv[0] = strdup(parameters_.executable.c_str());
  for (size_t i = 0; i < argc - 1; ++i) {
    const std::string &argument = parameters_.args[i];
    argv[i + 1] = strdup(argument.c_str());
  }
  argv[argc] = nullptr;

  childTry(execv(argv[0], argv) == 0,
           "failed to run \"" + parameters_.executable + "\"");
  childFailure("handleChild() has reaches the end");
  // double timeLimit = 2.0;
  // double idleLimit = 7.0;
  // TODO : handle the limit in msec
  // TODO : handle the realtime limit
  // TODO: if setting the child fails, we should get RUN_FAIL status, not
  // RUNTIME_ERROR
  // TODO: think of how to do this
  // TODO : FINISH IT !!!
}

void ProcessRunner::childRedirect(int fd, std::string fileName, int flags,
                                  mode_t mode) {
  if (fileName.empty()) {
    fileName = "/dev/null";
  }
  int dest_fd = open(fileName.c_str(), flags, mode);
  if (dest_fd < 0) {
    childFailure("unable to open \"" + fileName + "\"", errno);
  }
  if (dup2(dest_fd, fd) < 0) {
    childFailure("unable to duplicate file descriptor");
  }
}

[[noreturn]] void ProcessRunner::childFailure(const std::string &message,
                                              int errcode) {
  std::cerr << message << " " << strerror(errcode) << std::endl;
  // TODO : write to pipe
  _exit(42);
}

ProcessRunner::ProcessRunner() {}

}  // namespace UnixRunner
