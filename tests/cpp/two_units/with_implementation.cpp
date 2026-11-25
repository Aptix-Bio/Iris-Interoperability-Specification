// One of the two translation units of i2s_two_units: this one defines
// I2S_IMPLEMENTATION, so I2S.hpp's non-template function bodies are compiled
// here and only here. The program links only when every function the other
// unit calls is defined exactly once.
// RTM SingleHeader_02
#define I2S_IMPLEMENTATION
#include "I2S.hpp"

#include <cstdio>
#include <string>

std::string scanner_pairs(); // other_unit.cpp

int main()
{
    I2S::Attributes attributes;
    attributes[I2S::Attribute::ManufacturerModelName] = "GT450";
    const std::string expected = "Manufacturer=Leica;";
    const std::string found = scanner_pairs();
    if (found != expected || !attributes.to_pairs().has_value()) {
        std::fprintf(stderr, "i2s_two_units: expected '%s', found '%s'\n", expected.c_str(), found.c_str());
        return 1;
    }
    return 0;
}
