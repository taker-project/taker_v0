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

#include "utils.hpp"
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

namespace UnixRunner {

const int READ_PERM = S_IRUSR | S_IRGRP | S_IROTH;
const int WRITE_PERM = S_IWUSR | S_IWGRP | S_IWOTH;
const int EXEC_PERM = S_IXUSR | S_IXGRP | S_IXOTH;

int filePermissions(const char *fileName) {
  struct stat fileStats;
  if (stat(fileName, &fileStats) != 0) {
    return -1;
  }
  if (!S_ISREG(fileStats.st_mode)) {
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

}  // namespace UnixRunner
