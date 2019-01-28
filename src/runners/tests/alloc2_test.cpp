#include <iostream>
#include <vector>
#include "test_utils.hpp"

using namespace std;

int main() {
  for (int i = 0; i < 8; ++i) {
    std::vector<char> v1(10'000'000);
    std::vector<char> v2(10'000'000);
  }
  return 0;
}
