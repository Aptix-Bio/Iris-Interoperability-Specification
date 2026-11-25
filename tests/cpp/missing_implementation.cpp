// Built only by the ctest entry i2s_missing_implementation_fails_to_link,
// which passes when linking this program fails naming
// I2S::Attributes::to_pairs: no translation unit defines I2S_IMPLEMENTATION,
// so the bodies of I2S.hpp's non-template functions are compiled nowhere, and
// the linker reports each one called as an undefined symbol.
// RTM SingleHeader_02
#include "I2S.hpp"

int main()
{
    I2S::Attributes attributes;
    attributes[I2S::Attribute::Manufacturer] = "Leica";
    return attributes.to_pairs().has_value() ? 0 : 1;
}
