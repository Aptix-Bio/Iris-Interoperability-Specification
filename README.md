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
constant in namespace `I2S::Attribute` whose type carries the key's value
type, so an IDE completes the key names and the compiler refuses a value of
the wrong type. The whole vocabulary is listed at the top of the generated
`I2S_Keys.hpp`, one line per key.

```cpp
I2S::Attributes attributes;
attributes[I2S::Attribute::Manufacturer]          = "Leica";
attributes[I2S::Attribute::ManufacturerModelName] = "GT450";
attributes[I2S::Attribute::ScanTime]              = std::chrono::system_clock::now();
```

Each value is held as the text of its DICOM value representation (VR).

## Writing attributes from a DICOM file

`I2S::Attributes::from_dicom` asks a DICOM data set for each key's DICOM tag
(listed in `I2S::kKeys`) and keeps the text it returns, since each key's VR is
its DICOM attribute's. With [DCMTK](https://github.com/DCMTK/dcmtk) 3.7.1:

```c++
DcmFileFormat file;
if (file.loadFile("slide.dcm").bad()) return;
DcmDataset& dicom = *file.getDataset();

I2S::Attributes attributes = I2S::Attributes::from_dicom([&](I2S::DicomTag tag) -> std::optional<std::string> {
    OFString text; // every value, backslash-joined; OFTrue also searches sequence items
    if (dicom.findAndGetOFStringArray(DcmTagKey(tag.group, tag.element), text, OFTrue).bad()) return std::nullopt;
    return std::string(text.c_str());
});
attributes[I2S::Attribute::DII] = "S26-01234"; // the DII has no DICOM counterpart
```

`UniqueDeviceIdentifier` is read from an item of the `UDISequence`, which is
why the lookup searches sequence items. `DigitalImageIdentifier` and
`DigitalImageIdentifierIsPHI` have no DICOM counterpart and are written by
hand. A DICOM value I2S refuses (a DT without its UTC offset, say) is kept in
`attributes.errors()` until the key is written again.

## Writing attributes into an Iris slide

`attributes.to_pairs()` gives the (key name, value text) pairs that an Iris
File Extension (IFE) attribute block stores under `METADATA_I2S`. With IFE's
`Iris::File::Builder` writing the slide (`IFE_Builder.hpp`):

```c++
namespace blocks = Iris::File::blocks;
std::vector<blocks::AttributeSizeEntry> entries;
for (const I2S::Pair& pair : attributes.to_pairs().value()) // throws naming a refused write
    entries.push_back({.key = pair.key, .value = pair.value});
const Iris::File::Offset sizes_at = builder->append(blocks::AttributeSizesCreateInfo{.entries = entries});
const Iris::File::Offset bytes_at = builder->append(blocks::AttributeBytesCreateInfo{.entries = entries});
const Iris::File::Offset attributes_at = builder->append(blocks::AttributesCreateInfo{
    .FORMAT = Iris::File::constants::MetadataFormats::METADATA_I2S, .SIZES_OFFSET = sizes_at, .BYTES_OFFSET = bytes_at});
// attributes_at becomes the ATTRIBUTES_OFFSET of the slide's MetadataCreateInfo.
```

Iris-Slide's encoder does not yet take I2S attributes, and how the attribute
block's 16-bit VERSION carries an I2S version is not yet defined; both are
open in [development/WBS.md](development/WBS.md).

## Reading attributes

`I2S::Attributes::from_pairs` reads the pairs back. A viewer lists a file's I2S
attributes in one loop, in the specification's key order:

```cpp
for (const auto& element : attributes)
    std::cout << element.name() << " = " << element.text() << '\n';
```

A ```` ```cpp ```` block in this README is compiled and run as a test
(`cmake/readme_examples.cmake`); a ```` ```c++ ```` block needs a library I2S
does not build against (DCMTK, IFE) and is shown only.

## Status

**Draft 0.1, private.** The vocabulary is seeded with the Digital Image
Identifier and the scanner's identity only. Nothing here is stable until a
version is ratified, and no licence has been chosen yet.
