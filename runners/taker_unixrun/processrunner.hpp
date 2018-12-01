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
#include <sys/resource.h>
#include <sys/types.h>
#include <exception>
#include <map>
#include <vector>
#include "utils.hpp"

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

  enum class IsolatePolicy {
    NONE,
    NORMAL,
    COMPILE,
    STRICT
  };

  static IsolatePolicy strToIsolatePolicy(const std::string &value);

  struct Parameters {
    double timeLimit = 2.0;
    double idleLimit = 7.0;
    double memoryLimit = 256.0;
    bool clearEnv = false;
    std::string executable;
    std::map<std::string, std::string> env;
    std::vector<std::string> args;
    std::string workingDir = "";
    std::string stdinRedir = "";
    std::string stdoutRedir = "";
    std::string stderrRedir = "";
    std::string isolateDir = "";
    IsolatePolicy isolatePolicy = IsolatePolicy::NORMAL;

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

  Json::Value runnerInfoJson() const;

  Parameters &parameters();

  const Parameters &parameters() const;

  const RunResults &results() const;

  void execute();

  ProcessRunner();

 protected:
  void doExecute();
  [[noreturn]] void handleChild();
  void handleParent();

 private:
  Parameters parameters_ {};
  RunResults results_ {};
  pid_t pid_ = -1;
  int pipe_[2] {};
  struct timeval startTime_ {};

  void startTimer();
  double getTimerValue();

#ifdef __linux__
  bool updateTimeFromProcStat();
  bool updateMemFromProcStatus();
#endif

  void updateResultsOnRun();
  void updateVerdicts();
  void updateResultsOnTerminate(const struct rusage &resources, int status);

  void trySyscall(bool success, const std::string &errorName);

  void childRedirect(int fd, std::string fileName, int flags,
                     mode_t mode = 0644);

  std::string getFullErrorMessage(const std::string &message, int errcode = 0);
  [[noreturn]] void childFailure(const std::string &message, int errcode = 0);
  void parentFailure(const std::string &message, int errcode = 0);
};

}  // namespace UnixRunner

#endif  // PROCESSRUNNER_H
