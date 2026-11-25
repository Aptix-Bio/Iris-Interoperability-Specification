// Built only by the ctest entry i2s_compile_fail_flat_spelling, which passes when the
// compiler refuses the assignment below and its diagnostic names what the
// test expects (tests/CMakeLists.txt). A key is spelled one way,
// I2S::Attribute::Manufacturer (decided 2026-11-25); the flat spelling it
// replaced must not compile.
// RTM ReadableHeaders_01
#include "I2S_Attributes.hpp"

int main()
{
    I2S::Attributes attributes;
    attributes[I2S::Manufacturer] = "Leica";
    return 0;
}
