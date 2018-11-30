#ifndef _TEST_UTILS_HPP
#define _TEST_UTILS_HPP

#include <chrono>
#include <thread>

void sleep(int msec) {
  using namespace std::chrono;
  std::this_thread::sleep_for(milliseconds(msec));
}

void work(int msec) {
  using namespace std::chrono;
  steady_clock clock;
  auto start = clock.now();
  while (duration_cast<milliseconds>(clock.now() - start) < msec) {
    // do nothing
  }
}

#endif  // _TEST_UTILS_HPP
