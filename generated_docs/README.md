# generated_docs/

The AsciiDoc includes of the specification document (attributes, revision
history, value types, identity classes, the key table and the key sections),
written by `python -m generator` from `spec/*.json` at every CMake configure.
`spec/i2s_spec.adoc` includes each one; `cmake --build <build> --target
i2s_document` renders them to HTML and PDF. They are gitignored and carry a
DO-NOT-EDIT banner with the witness hash: change the JSON or the emitter in
`generator/emit/docs.py`, then regenerate.
