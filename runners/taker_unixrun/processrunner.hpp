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

#ifndef PROCESSRUNNER_H
#define PROCESSRUNNER_H

#include <json/json.h>
#include <exception>

namespace UnixRunner {

class RunnerError : public std::runtime_error {
 public:
  RunnerError(const std::string &comment);
};

class RunnerValidateError : public RunnerError {
 public:
  RunnerValidateError(const std::string &comment);
};

class ProcessRunner {
 public:
  // TODO : Document the Runner API!
  // TODO : Add privilege levels!

  enum class RunStatus {
    OK,
    TIME_LIMIT,
    IDLE_LIMIT,
    MEMORY_LIMIT,
    RUNTIME_ERROR,
    SECURITY_ERROR,
    RUN_FAIL,
    RUNNING,
    NONE
  };

  static const char *runStatusToStr(RunStatus status);

  struct Parameters {
    double timeLimit = 2.0;
    double idleLimit = 7.0;
    double memoryLimit = 256.0;
    std::string executable;
    std::vector<std::string> args;
    std::string workingDir = "";
    std::string stdinRedir = "";
    std::string stdoutRedir = "";
    std::string stderrRedir = "";

    void validate();
    void loadFromJsonStr(const std::string &json);
    void loadFromJson(const Json::Value &value);
  };

  struct RunResults {
    double time = 0.0;
    double clockTime = 0.0;
    double memory = 0.0;
    int exitCode = 0;
    int signal = 0;
    RunStatus status = RunStatus::NONE;
    std::string comment = "";

    std::string saveToJsonStr() const;
    Json::Value saveToJson() const;
  };

  Parameters &parameters();

  const Parameters &parameters() const;

  const RunResults &results() const;

  void execute();

  ProcessRunner();

 private:
  Parameters parameters_;
  RunResults results_;
};

}  // namespace UnixRunner

#endif  // PROCESSRUNNER_H
