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
#include <signal.h>
#include <sys/resource.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <cassert>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include "utils.hpp"

#ifndef _GNU_SOURCE
extern char **environ;
#endif

namespace UnixRunner {

pid_t g_activeChild = 0;

void termSignal(int) {
  if (g_activeChild != 0) {
    kill(g_activeChild, SIGKILL);
  }
  kill(0, SIGKILL);
}

class ActiveChildLock {
 private:
  struct sigaction oldActions_[3];

 public:
  ActiveChildLock(pid_t pid) {
    if (g_activeChild != 0) {
      throw std::runtime_error("active child already set");
    }
    g_activeChild = pid;
    struct sigaction sigHandler;
    zeroMem(sigHandler);
    for (int i = 0; i < 3; ++i) {
      zeroMem(oldActions_[i]);
    }
    sigHandler.sa_handler = termSignal;
    sigaction(SIGINT, &sigHandler, &oldActions_[0]);
    sigaction(SIGTERM, &sigHandler, &oldActions_[1]);
    sigaction(SIGQUIT, &sigHandler, &oldActions_[2]);
  }

  ~ActiveChildLock() {
    g_activeChild = 0;
    sigaction(SIGINT, &oldActions_[0], nullptr);
    sigaction(SIGTERM, &oldActions_[1], nullptr);
    sigaction(SIGQUIT, &oldActions_[2], nullptr);
  }
};

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
      throw std::runtime_error("env is not an object");
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

const char *ProcessRunner::runStatusToStr(ProcessRunner::RunStatus status) {
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
  if (signal != 0) {
    char *signalName = strsignal(signal);
    value["signal-name"] = (signalName == nullptr) ? "unknown" : signalName;
  }
  value["status"] = ProcessRunner::runStatusToStr(status);
  value["comment"] = comment;
  return value;
}

std::string ProcessRunner::RunResults::saveToJsonStr() const {
  return saveToJson().toStyledString();
}

ProcessRunner::Parameters &ProcessRunner::parameters() { return parameters_; }

const ProcessRunner::Parameters &ProcessRunner::parameters() const {
  return parameters_;
}

const ProcessRunner::RunResults &ProcessRunner::results() const {
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
  results_ = RunResults();
  results_.status = RunStatus::RUNNING;
  if (pipe2(pipe_, O_CLOEXEC) != 0) {
    throw RunnerError(getFullErrorMessage("unable to create pipe", errno));
  }
  pid_ = fork();
  if (pid_ < 0) {
    throw RunnerError(strerror(errno));
  }
  if (pid_ == 0) {
    close(pipe_[0]);
    try {
      handleChild();
    } catch (const std::exception &e) {
      childFailure(getFullExceptionMessage(e));
    }
  }
  ActiveChildLock lock(pid_);
  close(pipe_[1]);
  handleParent();
}

void ProcessRunner::handleParent() {
  startTimer();

  // check for RUN_FAIL
  int msgSize;
  int bytesRead = read(pipe_[0], &msgSize, sizeof(msgSize));
  if (bytesRead < 0) {
    parentFailure("unable to read from pipe", errno);
  }
  if (bytesRead > 0) {
    if (bytesRead != sizeof(msgSize)) {
      parentFailure("unexpected child/parent protocol error");
    }
    char *message = new char[msgSize + 1];
    message[msgSize] = 0;
    int bytesExpected = sizeof(char) * msgSize;
    trySyscall(read(pipe_[0], message, bytesExpected) == bytesExpected,
               "unexpected child/parent protocol error (message length"
               " must be " +
                   std::to_string(bytesExpected) + ", not " +
                   std::to_string(bytesRead) + ")");
    results_.status = RunStatus::RUN_FAIL;
    results_.comment = message;
    delete[] message;
    waitpid(pid_, nullptr, 0);
    return;
  }

  // initialize results
  results_.exitCode = results_.signal = 0;
  results_.time = results_.clockTime = 0.0;
  results_.memory = 0.0;
  results_.status = RunStatus::RUNNING;
  updateResultsOnRun();

  // wait for process
  while (results_.status == RunStatus::RUNNING) {
    int status = -1;
    struct rusage resources;
    zeroMem(resources);
    int pidWaited = wait4(pid_, &status, WNOHANG | WUNTRACED, &resources);
    if (pidWaited == -1) {
      // wait4() error
      int errCode = errno;
      kill(pid_, SIGKILL);
      parentFailure("unable to wait for process", errCode);
    }
    if (pidWaited == 0) {
      // the process is still running
      updateResultsOnRun();
      updateVerdicts();
      if (results_.status != RunStatus::RUNNING) {
        kill(pid_, SIGKILL);
        trySyscall(waitpid(pid_, nullptr, 0) >= 0,
                   "unable to wait for process");
        break;
      }
    } else {
      // the process has changed the state
      // FIXME : handle stopped/continued processes
      updateResultsOnTerminate(resources, status);
      if (results_.status == RunStatus::RUNNING) {
        kill(pid_, SIGKILL);
        waitpid(pid_, nullptr, 0);
        parentFailure(
            "unexpected process status: waitpid() returned, "
            "but the process is still alive (status = " +
            std::to_string(status) + ")");
      }
      updateVerdicts();
      break;
    }
    usleep(10'000);
  }
}

void ProcessRunner::startTimer() {
  zeroMem(startTime_);
  trySyscall(gettimeofday(&startTime_, nullptr) == 0,
             "could not get system time");
}

double ProcessRunner::getTimerValue() {
  struct timeval curTime;
  zeroMem(curTime);
  trySyscall(gettimeofday(&curTime, nullptr) == 0, "could not get system time");
  return timevalToDouble(timeDifference(startTime_, curTime));
}

bool ProcessRunner::updateResourcesFromProcInfo() {
#ifdef __linux__
  std::string procFileName = "/proc/" + std::to_string(pid_) + "/stat";
  std::ifstream procStats(procFileName);
  if (!procStats.good()) {
    return false;
  }
  std::string procStr;
  if (!std::getline(procStats, procStr)) {
    return false;
  }
  auto bracketPos = procStr.rfind(')');
  if (bracketPos == std::string::npos || bracketPos == procStr.size()) {
    return false;
  }
  procStr.erase(0, bracketPos + 1);
  std::istringstream tokenizer(procStr);
  unsigned long utime, stime, vsize;
  std::string unused;
  for (int field = 3; field <= 42; ++field) {
    if (field == 14) {
      tokenizer >> utime;
    } else if (field == 15) {
      tokenizer >> stime;
    } else if (field == 23) {
      tokenizer >> vsize;
    } else {
      tokenizer >> unused;
    }
    if (!tokenizer.good()) {
      return false;
    }
  }
  results_.time = 1.0 * (utime + stime) / sysconf(_SC_CLK_TCK);
  results_.memory = std::max(results_.memory, vsize / 1048576.0);
  return true;
#else
  // TODO : add code for *BSD (?)
  return false;
#endif
}

void ProcessRunner::updateResultsOnRun() {
  updateResourcesFromProcInfo();
  results_.clockTime = getTimerValue();
}

void ProcessRunner::updateVerdicts() {
  if (results_.time > parameters_.timeLimit) {
    results_.status = RunStatus::TIME_LIMIT;
  }
  if (results_.clockTime > parameters_.idleLimit) {
    results_.status = RunStatus::IDLE_LIMIT;
  }
  if (results_.memory > parameters_.memoryLimit) {
    results_.status = RunStatus::MEMORY_LIMIT;
  }
}

void ProcessRunner::updateResultsOnTerminate(const struct rusage &resources,
                                             int status) {
  if (WIFEXITED(status)) {
    results_.exitCode = WEXITSTATUS(status);
    if (results_.exitCode == 0) {
      results_.status = RunStatus::OK;
    } else {
      results_.status = RunStatus::RUNTIME_ERROR;
    }
  }
  if (WIFSIGNALED(status)) {
    results_.signal = WTERMSIG(status);
    results_.status = RunStatus::RUNTIME_ERROR;
  }
  results_.time =
      timevalToDouble(timeSum(resources.ru_stime, resources.ru_utime));
  results_.clockTime = getTimerValue();
  if (results_.memory == 0) {
    // FIXME : if the memory usage wasn't updated, maybe use smth better than
    // maxrss?
    results_.comment = "memory measurement is not precise!";
    results_.memory = resources.ru_maxrss / 1024.0;
  }
}

void ProcessRunner::trySyscall(bool success, const std::string &errorName) {
  if (success) {
    return;
  }
  if (pid_ == 0) {
    childFailure(errorName, errno);
  } else {
    parentFailure(errorName, errno);
  }
}

void ProcessRunner::handleChild() {
  setsid();

  int64_t integralTimeLimit =
      static_cast<int64_t>(ceil(parameters_.timeLimit + 0.2));
  trySyscall(updateLimit(RLIMIT_CPU, integralTimeLimit),
             "could not set time limit");

  int64_t memLimitBytes =
      static_cast<int64_t>(ceil(parameters_.memoryLimit * 1048576));
  trySyscall(updateLimit(RLIMIT_AS, memLimitBytes * 2),
             "could not set memory limit");
  trySyscall(updateLimit(RLIMIT_DATA, memLimitBytes * 2),
             "could not set memory limit");
  trySyscall(updateLimit(RLIMIT_STACK, memLimitBytes * 2),
             "could not set memory limit");

  if (!parameters_.workingDir.empty()) {
    trySyscall(chdir(parameters_.workingDir.c_str()) == 0,
               "could not change directory");
  }

  childRedirect(STDIN_FILENO, parameters_.stdinRedir, O_RDONLY);
  childRedirect(STDOUT_FILENO, parameters_.stdoutRedir,
                O_CREAT | O_TRUNC | O_WRONLY);
  childRedirect(STDERR_FILENO, parameters_.stderrRedir,
                O_CREAT | O_TRUNC | O_WRONLY);

  if (parameters_.clearEnv) {
    environ = nullptr;
  }
  for (const auto &iter : parameters_.env) {
    const std::string &key = iter.first;
    const std::string &value = iter.second;
    trySyscall(setenv(key.c_str(), value.c_str(), true) == 0,
               "could not set environment \"" + key + "\"");
  }

  size_t argc = parameters_.args.size() + 1;
  char **argv = new char *[argc + 1];
  argv[0] = strdup(parameters_.executable.c_str());
  for (size_t i = 0; i + 1 < argc; ++i) {
    const std::string &argument = parameters_.args[i];
    argv[i + 1] = strdup(argument.c_str());
  }
  argv[argc] = nullptr;

  trySyscall(execv(argv[0], argv) == 0,
             "failed to run \"" + parameters_.executable + "\"");
  childFailure("handleChild() has reached the end");
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

std::string ProcessRunner::getFullErrorMessage(const std::string &message,
                                               int errcode) {
  if (errcode == 0) {
    return message;
  } else {
    return message + ": " + strerror(errcode);
  }
}

[[noreturn]] void ProcessRunner::childFailure(const std::string &message,
                                              int errcode) {
  std::string fullMsg = getFullErrorMessage(message, errcode);
  int msgSize = static_cast<int>(fullMsg.size());
  write(pipe_[1], &msgSize, sizeof(msgSize));
  write(pipe_[1], fullMsg.c_str(), msgSize * sizeof(char));
  _exit(42);
}

void ProcessRunner::parentFailure(const std::string &message, int errcode) {
  throw RunnerError(getFullErrorMessage(message, errcode));
}

ProcessRunner::ProcessRunner() {}

}  // namespace UnixRunner
