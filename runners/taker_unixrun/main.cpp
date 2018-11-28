#include <json/json.h>
#include <iostream>
#include "processrunner.hpp"

int main() {
  using namespace UnixRunner;

  Json::Value value;
  std::cin >> value;

  ProcessRunner runner;
  runner.parameters().loadFromJson(value);
  runner.execute();
  std::cout << runner.results().saveToJson() << std::endl;

  return 0;
}
