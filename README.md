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

## Why it exists

A slide is given facts when it is scanned that never change afterwards: the
laboratory's identifier for it, its stain, the date and time of the scan, and
the identity of the scanner, down to its unique device identifier. These are
characteristics of the slide, kept apart from the patient's clinical metadata
(HL7 v2 or FHIR). I2S names them so that every scanner's output can be
written with one vocabulary.

An `.iris` file that marks its attributes `METADATA_I2S` promises that every
pair is a fact fixed when the slide was scanned that identifies no individual;
clinical and identifying facts travel in IFE's clinical metadata stream
instead. I2S keys follow DICOM keywords where DICOM has the fact, and diverge
where it does not: `DigitalImageIdentifier` (DII), the laboratory's accession
identifier for the slide, has no DICOM keyword.

## Status

**Draft 0.1, private.** The vocabulary is seeded with the Digital Image
Identifier and the scanner's identity only. Nothing here is stable until a
version is ratified, and no licence has been chosen yet.
