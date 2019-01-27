#include <cstdlib>
#include <iostream>
#include <string>

using namespace std;

int main() {
  char *env = getenv("HELLO");
  std::cout << (env == nullptr ? string("none") : string("env=") + env)
            << std::endl;
  return 0;
}
