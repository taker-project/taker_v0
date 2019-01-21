#include <iostream>
#include <vector>
#include "test_utils.hpp"

using namespace std;

int main() {
  { std::vector<char> v(60'000'000); }
  { std::vector<char> v(20'000'000); }
  { std::vector<char> v(30'000'000); }
  return 0;
}
