// The second translation unit of i2s_two_units: it includes I2S.hpp without
// I2S_IMPLEMENTATION, as every .cpp of a program but one does, and calls the
// functions whose bodies the other unit compiles.
// RTM SingleHeader_02
#include "I2S.hpp"
#include "I2S.hpp" // a second include in one unit is harmless: I2S.hpp is include-guarded

#include <string>
#include <vector>

std::string scanner_pairs()
{
    I2S::Attributes attributes;
    attributes[I2S::Attribute::Manufacturer] = "Leica";
    // The Result is named: value() returns a reference into it, which a
    // range-for over attributes.to_pairs().value() would leave dangling.
    const I2S::Result<std::vector<I2S::Pair>> pairs = attributes.to_pairs();
    std::string text;
    for (const I2S::Pair& pair : pairs.value()) {
        text += pair.key + "=" + pair.value + ";";
    }
    return text;
}
