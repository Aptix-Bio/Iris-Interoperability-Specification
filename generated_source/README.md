# generated_source/

Written by `python -m generator` at every CMake configure, gitignored, and
carrying a DO-NOT-EDIT banner:

- `I2S.hpp`, the one header a program includes and CMake installs: the
  vocabulary, then the public declarations and the implementation, copied
  from the hand-written sources in `include/` between their
  `// BEGIN I2S.hpp` and `// END I2S.hpp` markers. Exactly one `.cpp` of a
  program defines `I2S_IMPLEMENTATION` before including it.
- `I2S_Keys.hpp`, the vocabulary alone, which the sources in `include/`
  include while they are edited. It opens with one typed constant per key and
  short name in `I2S::Attribute`, each documented as an IDE shows on hover,
  then the version, the scoped enumerations and the constexpr tables.

Change the JSON, the emitter in `generator/emit/cpp.py` or a source in
`include/`, then reconfigure.
