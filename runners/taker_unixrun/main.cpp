#include <json/json.h>
#include <cstring>
#include <iostream>
#include "processrunner.hpp"

int main(int argc, char **argv) {
  using namespace UnixRunner;

  if (argc == 2 && strcmp(argv[1], "-?") == 0) {
    std::cout << ProcessRunner().runnerInfoJson() << std::endl;
    return 0;
  }

  Json::Value value;
  std::cin >> value;

  ProcessRunner runner;
  runner.parameters().loadFromJson(value);
  runner.execute();
  std::cout << runner.results().saveToJson() << std::endl;

  return 0;
}
