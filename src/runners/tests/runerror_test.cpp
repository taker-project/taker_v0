#include <cassert>
#include <cstdlib>
#include <iostream>
#include <string>

using namespace std;

int main() {
  std::string s;
  std::cin >> s;
  if (s == "assert") {
    assert(false);
  } else if (s == "error") {
    return 1;
  }
  return 0;
}
