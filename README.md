# Iris Interoperability Specification (I2S)

I2S is the vocabulary of slide-level facts that a whole-slide image carries
from the moment it is scanned: what the slide is (its Digital Slide
Identifier) and which device scanned it, and later its stain and the time it
was scanned. Each fact is a named key with a stated value type, its DICOM
counterpart where one exists, and an identity class saying whether it can
identify a person.

The specification is a versioned, append-only JSON document (`spec/`) that a
generator (`generator/`) compiles into a C++20 header and a readable
specification document, as the Iris File Extension (IFE) does with its own
`spec/*.json`. A key that is renamed in the JSON breaks every program that
uses its old name at compile time, so the JSON stays the one source.

## Why it exists

Ryan Landvater, 2026-11-24:

> "We will need to make a I2S repo as well … the information that goes into
> the slide when it is initially scanned by different scanners (acessioning
> number, stain info, time, date, scanner info like unique device ID). These
> are the things that need to go into I2S because they're indelible
> characteristics of the slide and not patient HL7 metadata."

> "We'll call the accessioning number DigitalSlideIdentifier(DSI)"

> "let's have I2S be a JSON specification that gets compiled into C++ source
> like the IFE"

An `.iris` file that marks its attributes `METADATA_I2S` promises that every
pair is a fact fixed when the slide was scanned that identifies no individual;
clinical and identifying facts travel in IFE's clinical metadata stream (HL7
v2 or FHIR) instead. I2S keys follow DICOM keywords where DICOM has the fact,
and diverge where it does not: `DigitalSlideIdentifier` has no DICOM keyword.

## Status

**Draft 0.1, private.** The vocabulary is seeded with the Digital Slide
Identifier and the scanner's identity only. Nothing here is stable until a
version is ratified, and no licence has been chosen yet.
