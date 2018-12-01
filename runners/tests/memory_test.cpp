#include "test_utils.hpp"

int main() {
  const int ITERS = 1;
  const int MEM_SIZE = 64'000'000;
  for (int i = 0; i < ITERS; ++i) {
    char volatile *mem = new char[MEM_SIZE];
    for (int j = 0; j < MEM_SIZE; ++j) {
      mem[j] = 'a';
    }
    (void)mem;
  }
  return 0;
}
