// Built only by the ctest entry i2s_renamed_key_fails_to_compile, which passes
// when the compiler rejects this file naming DigitalSlideIdentifier: the key's
// name before it was renamed DigitalImageIdentifier in spec/i2s_keys.json
// (2026-11-24). The generated enumeration has no such enumerator, so a
// consumer still using the old name fails to build instead of the old name
// falling back to some other key at run time.
// RTM Generated_04
#include "I2S.hpp"

int main()
{
    return static_cast<int>(I2S::Key::DigitalSlideIdentifier);
}
