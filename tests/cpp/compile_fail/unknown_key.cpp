// Built only by the ctest entry i2s_compile_fail_unknown_key, which passes when the
// compiler refuses the assignment below and its diagnostic names what the
// test expects (tests/CMakeLists.txt).
// RTM TypedKeys_01
#include "I2S_Attributes.hpp"

int main()
{
    I2S::Attributes attributes;
    attributes[I2S::Attribute::NoSuchKey] = "Leica";
    return 0;
}
