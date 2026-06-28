/**
 * BBL C++ Runtime Library
 * Contains runtime helpers and definitions for Baybayin Language (BBL).
 */

#ifndef BBL_RUNTIME_HPP
#define BBL_RUNTIME_HPP

#include <iostream>
#include <string>

namespace bbl {
    template <typename T>
    void ipakita(const T& val) {
        std::cout << val << std::endl;
    }
}

#endif // BBL_RUNTIME_HPP
