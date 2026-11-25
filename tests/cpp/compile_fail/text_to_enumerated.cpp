// Built only by the ctest entry i2s_compile_fail_text_to_enumerated, which passes when the
// compiler refuses the assignment below and its diagnostic names what the
// test expects (tests/CMakeLists.txt): an ENUMERATED key takes its generated
// enumeration, I2S::FocusMethod, and no text.
// RTM Enumerated_01
#include "I2S.hpp"

int main()
{
    I2S::Attributes attributes;
    attributes[I2S::Attribute::FocusMethod] = "AUTO";
    return 0;
}
