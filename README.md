# Iris Interoperability Specification (I2S)

I2S is the vocabulary of facts a whole-slide image carries from the moment it
is scanned: its Digital Image Identifier, the device that scanned it, and how
and when it was scanned. Each fact is a named key with a stated value type,
its DICOM counterpart where one exists, and an identity class saying whether
it can identify a person.

## Providence
**Iris splits acquisition metadata from optional patient information**

I2S records what the scanner knows at scan time, including what it reads from
the slide's label. Those facts never change, so they are written once into the
slide file as indelible acquisition metadata (`METADATA_I2S` in an IFE file).

Clinical data does not belong here. What the laboratory information system or
the health record knows (specimen preparation, stain, anatomic site,
diagnosis, patient identity) changes after the scan and travels separately, as
HL7/FHIR: optionally inside the slide, in IFE's clinical metadata stream,
which can be removed without touching the image. DICOM keeps both in one
record; mutable clinical metadata inside an immutable image container carries
more risk than benefit [1, 2].

The values that a renderer needs (pixel spacing, magnification, focal planes) and that are integral to the proper display of an image are part of the IFE format itself, not I2S keys.

1. P. Gershkovich, "Wearing a fur coat in the summertime: Should digital
   pathology redefine medical imaging?" *Journal of Pathology Informatics* 18,
   100450 (2025). <https://doi.org/10.1016/j.jpi.2025.100450>
2. P. Gershkovich, "Digital Pathology Standards: A Response to WG-26."
   *Journal of Pathology Informatics* 19, 100510 (2025).
   <https://doi.org/10.1016/j.jpi.2025.100510>

## Adding Keys to I2S

If you believe additional keys should be added to I2S, please open a [github issue](https://github.com/Aptix-Bio/Iris-Interoperability-Specification/issues) and we will review the request for addition into the keys for future versions. Include DICOM Tag if it corresponds with an established entry.

## Using I2S

I2S installs one header, `I2S.hpp`, and a CMake package:

```bash
cmake --preset release && cmake --build --preset release
cmake --install build/release --prefix <prefix>
```

```cmake
find_package(I2S 0.1 REQUIRED CONFIG)   # with <prefix> on CMAKE_PREFIX_PATH
target_link_libraries(scanner PRIVATE I2S::i2s)
```

Every source file includes `<I2S.hpp>`. Exactly one `.cpp` of a program
writes `#define I2S_IMPLEMENTATION` before its `#include <I2S.hpp>`, which
compiles the bodies of I2S's non-template functions there and nowhere else.
Without that `.cpp`, linking fails with undefined references to I2S's
functions (`I2S::Attributes::to_pairs() const`, say); with two, it fails with
duplicate definitions of them.

## Writing attributes

A scanner writes I2S attributes through `I2S.hpp`. Each key is a constant in
namespace `I2S::Attribute` whose type carries the key's value type, so an IDE
completes the key names and the compiler refuses a value of the wrong type.
The constants open the header, each with its full description, value type,
VR, multiplicity, DICOM attribute and identity class, which is what an IDE
shows on hover.

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
File Extension (IFE) attribute block stores under `METADATA_I2S`. Iris-Slide's
encoder takes them in `IrisSlide::EncodeSlideInfo::attributes` (Iris-Headers'
`IrisSlideTypes.hpp`) with the I2S version, and writes them as the slide's
attribute block in place of any pairs the source file carried
(`IrisSlideCore.hpp`):

```c++
IrisSlide::EncodeSlideInfo info {.srcFilePath = "slide.svs", .desiredEncoding = IrisSlide::TILE_ENCODING_JPEG};
info.attributes.type    = IrisSlide::METADATA_I2S;
info.attributes.version = I2S::kIfeAttributesVersion; // major << 8 | minor: 0.1 is 0x0001
const auto pairs = attributes.to_pairs(); // named: a range-for over to_pairs().value() would read a destroyed temporary
for (const I2S::Pair& pair : pairs.value()) // throws naming a refused write
    info.attributes[pair.key] = std::u8string(pair.value.begin(), pair.value.end());
IrisSlide::Encoder encoder = IrisSlide::create_encoder(info);
Iris::Result result = IrisSlide::dispatch_encoder(encoder); // fails naming a pair IFE cannot hold
```

I2S checks the keys and the value text; the encoder checks only what IFE's
attribute block requires (ASCII keys, UTF-8 values, sizes) and refuses
version 0. The attribute block's 16-bit VERSION carries the I2S version as
`major << 8 | minor` (decided 2026-11-25, and stated in IFE's ife-attributes
clause), which the header emits as `I2S::kIfeAttributesVersion`; 0 is an
unversioned claim, which IFE reads as free text.

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
