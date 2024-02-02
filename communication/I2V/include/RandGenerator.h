#ifndef RANDGENERATOR_H
#define RANDGENERATOR_H

// Not thread safe (unless auto-initialization is avoided and each thread has
// its own RandGenerator object)

#include <iostream>
#include <random>
#include <chrono>

class RandGenerator {
public:
    typedef unsigned int uint32;
    std::mt19937* generator;

    explicit RandGenerator();
    ~RandGenerator();
    explicit RandGenerator(int seed) {
        generator = new std::mt19937(seed);
    }
    void seed( uint s );
    void seed();
    uint32 randInt();
    uint32 randInt( int );
    double rand();
};

inline RandGenerator::RandGenerator() {
    generator = new std::mt19937();
}

inline RandGenerator::~RandGenerator() {
    delete generator;
}

inline void RandGenerator::seed() {
    unsigned s = std::chrono::system_clock::now().time_since_epoch().count();
    seed(s);
}

inline void RandGenerator::seed(uint s) {
    delete generator;
    generator = new std::mt19937(s);
}

inline RandGenerator::uint32 RandGenerator::randInt() {
    return (uint32)(*generator)();
}

inline RandGenerator::uint32  RandGenerator::randInt(int n) {
    return randInt() % n;
}

inline double RandGenerator::rand() {
    return (double)(randInt())/(generator -> max());
}




#endif