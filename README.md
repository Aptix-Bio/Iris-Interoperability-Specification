# Iris Interoperability Specification (I2S)

I2S is the vocabulary of slide-level facts that a whole-slide image carries
from the moment it is scanned: what the slide is (its Digital Image
Identifier) and which device scanned it, and later its stain and the time it
was scanned. Each fact is a named key with a stated value type, its DICOM
counterpart where one exists, and an identity class saying whether it can
identify a person.

The specification is a versioned, append-only JSON document (`spec/`) that a
generator (`generator/`) compiles into a C++20 header and a readable
specification document, as the Iris File Extension (IFE) does with its own
`spec/*.json`. A key that is renamed in the JSON breaks every program that
uses its old name at compile time, so the JSON stays the one source.

## Providence
**Iris splits acquisition metadata from optional patient information**

DICOM blends immutable / indelible file attributes with clinical metadata
(protected patient health information). Iris instead splits file / laboratory
metadata such as the acquisition metadata, timing, and unique digital image
identifier from the clinical metadata that may be patient identifiable. 

Clinical information can be optionally encoded in a iris slide but not within
the `METADATA_I2S` and instead should be encoded within the clinical metadata
block within HL7 compatible streams.

## Writing attributes

A scanner writes I2S attributes through `I2S_Attributes.hpp`. Each key is a
constant in namespace `I2S` whose type carries the key's value type, so an IDE
completes the key names and the compiler refuses a value of the wrong type:

```cpp
I2S::Attributes attributes;
attributes[I2S::Manufacturer]          = "Leica";
attributes[I2S::ManufacturerModelName] = "GT450";
attributes[I2S::ScanTime]              = std::chrono::system_clock::now();
```

Each value is held as the text of its DICOM value representation, and
`attributes.to_pairs()` gives the (key name, value text) pairs an IFE
attribute block stores under `METADATA_I2S`; `I2S::Attributes::from_pairs`
reads them back. A viewer lists a file's I2S attributes in one loop, in the
specification's key order:

```cpp
for (const auto& element : attributes)
    std::cout << element.name() << " = " << element.text() << '\n';
```

## Status

**Draft 0.1, private.** The vocabulary is seeded with the Digital Image
Identifier and the scanner's identity only. Nothing here is stable until a
version is ratified, and no licence has been chosen yet.
