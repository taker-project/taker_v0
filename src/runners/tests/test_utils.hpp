#ifndef _TEST_UTILS_HPP
#define _TEST_UTILS_HPP

#include <time.h>
#include <chrono>
#include <thread>

namespace TestUtils {

void sleep(int msec) {
  using namespace std::chrono;
  std::this_thread::sleep_for(milliseconds(msec));
}

void work(int msec) {
  clock_t start = clock();
  while (static_cast<int64_t>(clock() - start) <
         static_cast<int64_t>(CLOCKS_PER_SEC) * msec / 1000) {
    // do nothing
  }
}

}  // namespace TestUtils

#endif  // _TEST_UTILS_HPP
