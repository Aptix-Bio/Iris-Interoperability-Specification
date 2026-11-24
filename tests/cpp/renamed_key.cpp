// Built only by the ctest entry i2s_renamed_key_fails_to_compile, which passes
// when the compiler rejects this file naming AccessionNumber. It stands for a
// consumer still using a key's old name after the key was renamed in
// spec/i2s_keys.json (the DSI was the accessioning number): the generated
// enumeration has no such enumerator, so the build breaks instead of the old
// name falling back to some other key at run time.
// RTM Generated_04
#include "I2S_Keys.hpp"

int main()
{
    return static_cast<int>(I2S::Key::AccessionNumber);
}
