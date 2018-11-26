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
#include <unistd.h>
#include <sstream>
#include "utils.hpp"

namespace UnixRunner {

RunnerError::RunnerError(const std::string &comment)
    : std::runtime_error(comment) {}

RunnerValidateError::RunnerValidateError(const std::string &comment)
    : RunnerError(comment) {}

void ProcessRunner::Parameters::validate() {
#define VALIDATE_ASSERT(cond) \
  if (!(cond)) throw RunnerValidateError(#cond);
  VALIDATE_ASSERT(timeLimit > 0);
  VALIDATE_ASSERT(idleLimit > 0);
  VALIDATE_ASSERT(memoryLimit > 0);
  VALIDATE_ASSERT(fileIsExecutable(executable));
  VALIDATE_ASSERT(workingDir.empty() || directoryIsGood(workingDir));
  VALIDATE_ASSERT(stdinRedir.empty() || fileIsReadable(stdinRedir));
  VALIDATE_ASSERT(stdoutRedir.empty() || fileIsWritable(stdoutRedir));
  VALIDATE_ASSERT(stderrRedir.empty() || fileIsWritable(stderrRedir));
#undef VALIDATE_ASSERT
}

void ProcessRunner::Parameters::loadFromJson(const Json::Value &value) {
  using Json::Value;
  timeLimit = value.get("time-limit", Value(timeLimit)).asDouble();
  idleLimit = value.get("idle-limit", Value(timeLimit * 3.5)).asDouble();
  memoryLimit = value.get("memory-limit", Value(memoryLimit)).asDouble();
  executable = value.get("executable", Value("")).asString();
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

ProcessRunner::ProcessRunner() {}

}  // namespace UnixRunner
