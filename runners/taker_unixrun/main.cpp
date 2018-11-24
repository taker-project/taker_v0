#include <iostream>
#include "json/json.h"

int main(int argc, char **argv) {
    Json::Value val;
    std::cin >> val;
    std::cout << val["message"].asString() << std::endl;
    std::cout << val << std::endl;
    return 0;
}
