/*
 * Copyright (C) 2018-2019  Alexander Kernozhitsky <sh200105@mail.ru>
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

#include "utils.hpp"
#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <sys/resource.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <algorithm>
#include <cassert>
#include <typeinfo>

#ifdef __GNUC__
#include <cxxabi.h>
#endif

namespace UnixRunner {

OSError::OSError(const std::string &comment) : std::runtime_error(comment) {}

DirectoryChanger::DirectoryChanger(const std::string &dirName)
    : oldDirName_(nullptr) {
  if (dirName.empty()) {
    return;
  }
  oldDirName_ = new char[PATH_MAX + 2];
  if (getcwd(oldDirName_, PATH_MAX + 1) == nullptr) {
    throw OSError(
        getFullErrorMessage("unable to get working directory", errno));
  }
  if (chdir(dirName.c_str())) {
    throw OSError(getFullErrorMessage(
        "unable to change directory to + \"" + dirName + "\"", errno));
  }
}

DirectoryChanger::~DirectoryChanger() {
  if (oldDirName_ == nullptr) {
    return;
  }
  chdir(oldDirName_);  // we are in destructor, so ignore all the errors here
  delete[] oldDirName_;
}

FileDescriptorOwner::FileDescriptorOwner(int fd) : fd_(fd) {}

int FileDescriptorOwner::getFileDescriptor() const { return fd_; }

FileDescriptorOwner::~FileDescriptorOwner() { close(fd_); }

double Timer::getTime() const {
  using namespace std::chrono;
  return 1e-9 * duration_cast<nanoseconds>(clock_.now() - startTime_).count();
}

void Timer::start() { startTime_ = clock_.now(); }

Timer::Timer() { start(); }

const int READ_PERM = S_IRUSR | S_IRGRP | S_IROTH;
const int WRITE_PERM = S_IWUSR | S_IWGRP | S_IWOTH;
const int EXEC_PERM = S_IXUSR | S_IXGRP | S_IXOTH;

int filePermissions(const char *fileName) {
  struct stat fileStats;
  zeroMem(fileStats);
  if (stat(fileName, &fileStats) != 0) {
    return -1;
  }
  int fileType = fileStats.st_mode & S_IFMT;
  if (fileType != S_IFREG && fileType != S_IFLNK && fileType != S_IFBLK &&
      fileType != S_IFCHR) {
    return -1;
  }
  if (fileStats.st_uid == getuid()) {
    return (fileStats.st_mode & S_IRWXU);
  }
  if (fileStats.st_gid == getgid()) {
    return (fileStats.st_mode & S_IRWXG);
  }
  return (fileStats.st_mode & S_IRWXO);
}

bool fileIsGood(const char *fileName) { return filePermissions(fileName) >= 0; }

bool fileIsGood(const std::string &fileName) {
  return fileIsGood(fileName.c_str());
}

bool directoryIsGood(const char *fileName) {
  struct stat fileStats;
  zeroMem(fileStats);
  if (stat(fileName, &fileStats) != 0) {
    return false;
  }
  return S_ISDIR(fileStats.st_mode);
}

bool directoryIsGood(const std::string &fileName) {
  return directoryIsGood(fileName.c_str());
}

bool fileIsReadable(const char *fileName) {
  int permissions = filePermissions(fileName);
  return permissions >= 0 && (permissions & READ_PERM) != 0;
}

bool fileIsReadable(const std::string &fileName) {
  return fileIsReadable(fileName.c_str());
}

bool fileIsWritable(const char *fileName) {
  int permissions = filePermissions(fileName);
  return permissions >= 0 && (permissions & WRITE_PERM) != 0;
}

bool fileIsWritable(const std::string &fileName) {
  return fileIsReadable(fileName.c_str());
}

bool fileIsExecutable(const char *fileName) {
  int permissions = filePermissions(fileName);
  return permissions >= 0 && (permissions & EXEC_PERM) != 0;
}

bool fileIsExecutable(const std::string &fileName) {
  return fileIsExecutable(fileName.c_str());
}

bool updateLimit(int resource, int64_t value) {
  struct rlimit rlim;
  zeroMem(rlim);
  if (getrlimit(resource, &rlim) != 0) {
    return false;
  }
  if (rlim.rlim_max == RLIM_INFINITY) {
    rlim.rlim_cur = value;
  } else {
    rlim.rlim_cur = std::min(static_cast<rlim_t>(value), rlim.rlim_max);
  }
  rlim.rlim_max = rlim.rlim_cur;
  if (setrlimit(resource, &rlim) != 0) {
    return false;
  }
  return true;
}

#ifdef __GNUC__
std::string demangle(const char *typeName) {
  int status = -1;
  char *demangled = abi::__cxa_demangle(typeName, 0, 0, &status);
  assert(status == 0);
  std::string res = demangled;
  free(demangled);
  return res;
}
#else
std::string demangle(const char *typeName) { return typeName; }
#endif

std::string getFullExceptionMessage(const std::exception &exc) {
  return std::string("") + demangle(typeid(exc).name()) + ": " + exc.what();
}

const int USEC_IN_SECOND = 1'000'000;

struct timeval timeSum(const struct timeval &val1, const struct timeval &val2) {
  struct timeval res;
  zeroMem(res);
  res.tv_sec = val1.tv_sec + val2.tv_sec;
  res.tv_usec = val1.tv_usec + val2.tv_usec;
  if (res.tv_usec >= USEC_IN_SECOND) {
    ++res.tv_sec;
    res.tv_usec -= USEC_IN_SECOND;
  }
  return res;
}

struct timeval timeDifference(const struct timeval &start,
                              const struct timeval &finish) {
  struct timeval res;
  zeroMem(res);
  res.tv_sec = finish.tv_sec - start.tv_sec;
  res.tv_usec = finish.tv_usec - start.tv_usec;
  if (res.tv_usec < 0) {
    --res.tv_sec;
    res.tv_usec += USEC_IN_SECOND;
  }
  return res;
}

double timevalToDouble(const struct timeval &value) {
  return 1.0 * value.tv_sec + 1.0 * value.tv_usec / USEC_IN_SECOND;
}

std::string getFullErrorMessage(const std::string &message, int errcode) {
  if (errcode == 0) {
    return message;
  } else {
    return message + ": " + strerror(errcode);
  }
}

bool redirectDescriptor(int fd, std::string fileName, int flags, mode_t mode) {
  if (fileName.empty()) {
    fileName = "/dev/null";
  }
  int dest_fd = open(fileName.c_str(), flags, mode);
  if (dest_fd < 0) {
    return false;
  }
  if (dup2(dest_fd, fd) < 0) {
    int dupErr = errno;
    close(dest_fd);
    errno = dupErr;
    return false;
  }
  return true;
}

}  // namespace UnixRunner
