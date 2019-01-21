#include <vector>
#include "test_utils.hpp"

int main() {
  std::vector<char> vec;
  for (int i = 0; i < 64'000'000; ++i) {
    vec.push_back(i);
  }
  return 0;
}
