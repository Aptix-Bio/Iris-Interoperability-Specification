// The one translation unit of a program built against an installed I2S: it
// includes only <I2S.hpp>, twice (the include guard makes the second
// harmless), and defines I2S_IMPLEMENTATION so the function bodies compile
// here.
// RTM SingleHeader_03
#define I2S_IMPLEMENTATION
#include <I2S.hpp>
#include <I2S.hpp>

#include <cstdio>

int main()
{
    I2S::Attributes attributes;
    attributes[I2S::Attribute::Manufacturer] = "Leica";
    attributes[I2S::Attribute::DII] = "S26-01234";
    const I2S::Result<std::vector<I2S::Pair>> pairs = attributes.to_pairs();
    if (!pairs.has_value() || pairs.value().size() != 2) {
        std::fprintf(stderr, "i2s_install_consumer: expected 2 pairs from the installed I2S.hpp\n");
        return 1;
    }
    return 0;
}
