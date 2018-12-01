#include <cstdlib>
#include <iostream>

using namespace std;

int main() {
  auto ptr = getenv("HELLO");
  std::cout << (ptr == nullptr ? "none" : ptr) << std::endl;
  return 0;
}
