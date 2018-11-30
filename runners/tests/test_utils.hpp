#ifndef _TEST_UTILS_HPP
#define _TEST_UTILS_HPP

#include <chrono>
#include <thread>

namespace TestUtils {

void sleep(int msec) {
  using namespace std::chrono;
  std::this_thread::sleep_for(milliseconds(msec));
}

void work(int msec) {
  using namespace std::chrono;
  steady_clock clock;
  auto start = clock.now();
  while (clock.now() - start < milliseconds(msec)) {
    // do nothing
  }
}

}  // namespace TestUtils

#endif  // _TEST_UTILS_HPP

