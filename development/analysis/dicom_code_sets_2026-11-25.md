# DICOM code sets for stain and fixative, and where those facts live

Research date: 2026-11-25. Every DICOM page below was read live at edition
2026e; every FHIR page at R5 (5.0.0) and R4 (4.0.1). Written for
CodeSets_5.2 (a `CODE` value type with stain and fixative as its first users)
and kept after Decision_17 moved stain and fixative to FHIR, since it records
why.

## 1. CID 8112 Specimen Stain

https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_8112.html

- Keyword `SpecimenStain`, FHIR keyword `dicom-cid-8112-SpecimenStain`, UID
  1.2.840.10008.6.1.1050, version 20240611, **Extensible**.
- 217 rows, every one coding scheme designator `SCT` (SNOMED CT), no repeated
  code value. Machine-readable as a FHIR ValueSet:
  http://dicom.nema.org/medical/dicom/resources/valuesets/fhir/json/ValueSet-dicom-cid-8112-SpecimenStain.json
  (system `http://snomed.info/sct`; legacy SNOMED-RT codes beside it under
  `http://snomed.info/srt`).
- Examples (designator, value, meaning as the table prints it):
  SCT 12710003 hematoxylin stain; SCT 36879007 water soluble eosin stain;
  SCT 83600004 spirit soluble eosin stain; SCT 1346008 blue shade eosin stain;
  SCT 373646006 giemsa stain; SCT 255808002 periodic acid Schiff stain;
  SCT 406989007 trichrome stain; SCT 255813003 Ziehl-Neelsen stain.
- **There is no single H&E code.** No row contains "&" or "and eosin".
- Code meanings are capitalized inconsistently ("hematoxylin stain", "Congo red
  stain"), and the rows are not alphabetical (fluorescent and Sudan entries
  were appended after Ziehl-Neelsen).

## 2. CID 8114 Specimen Fixative

https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_8114.html

Keyword `SpecimenFixative`, UID 1.2.840.10008.6.1.1052, version 20250122,
**Extensible**. The full table, in order:

| Designator | Value | Meaning |
|---|---|---|
| SCT | 434162003 | Neutral Buffered Formalin |
| SCT | 433474002 | Bouin's fluid |
| SCT | 431510009 | Formalin |
| SCT | 433338005 | Carnoy's fluid |
| SCT | 434295000 | Formol sublimate |
| SCT | 433471005 | Helly's fluid |
| SCT | 430028007 | Michel's medium |
| SCT | 433473008 | Zenker's fluid |
| SCT | 52836003 | Paraformaldehyde |
| SCT | 2869004 | Acetic acid |
| SCT | 259153006 | Chloroform |
| SCT | 430821002 | Chromium trioxide |
| SCT | 419442005 | Ethanol |
| SCT | 111095003 | Formaldehyde |
| SCT | 11496005 | Mercuric chloride |
| SCT | 259221006 | Methanol |
| SCT | 13931001 | Osmium tetroxide |
| SCT | 24215009 | Picric acid |
| SCT | 19893005 | Potassium dichromate |
| NCIt | C185113 | PAXgene Tissue System |

The last row is the only one outside SNOMED CT.

## 3. How DICOM records them

PS3.3 C.7.6.22 Specimen Module, Table C.7.6.22-2:
https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.22.html

```
Specimen Description Sequence (0040,0560)               Type 1, one item per specimen
> Specimen Preparation Sequence (0040,0610)              Type 2, one item per step, ascending time (C.7.6.22.1.3)
>> Specimen Preparation Step Content Item Sequence (0040,0612)   Type 1, BTID 8001
>>> Content Item Macro (PS3.3 Table 10-2): Value Type (0040,A040),
    Concept Name Code Sequence (0040,A043), Concept Code Sequence (0040,A168) for CODE
```

Each content item carries one code (Table 10-2,
https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_10.2.html).

PS3.16 templates, all on
https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_C.html
(anchors `#sect_TID_8001` to `#sect_TID_8004`):

- **TID 8001 Specimen Preparation** (one step): row 3, (111701, DCM,
  "Processing type"), CODE, M, DCID 8111; row 9 includes TID 8003 when the
  processing type is (127790008, SCT, "Staining"); **row 10, (430864009, SCT,
  "Tissue Fixative"), CODE, VM 1, U, BCID 8114**; row 11, (430863003, SCT,
  "Embedding medium"), BCID 8115.
- **TID 8003 Specimen Staining**: row 1, **(424361007, SCT, "Using
  substance"), CODE, VM 1-n, DCID 8112**, required if row 2 is absent; row 2,
  the same concept as TEXT, VM 1, required if row 1 is absent.
- CID 8111 Specimen Preparation Procedure
  (https://dicom.nema.org/medical/dicom/current/output/chtml/part16/sect_CID_8111.html)
  has no fixation type; PS3.17's example puts the fixative on a (9265001, SCT,
  "Specimen processing") step.

**H&E is two "Using substance" items** in one staining step. PS3.17 Table
NN.6-4
(https://dicom.nema.org/medical/dicom/current/output/chtml/part17/sect_NN.6.2.html)
writes step 6 as Processing type = (127790008, SCT, "Staining"), Using
substance = (12710003, SCT, "hematoxylin stain"), Using substance =
(36879007, SCT, "water soluble eosin stain"). The same example codes its
fixative as (111095003, SCT, "Formalin"), which CID 8114 calls Formaldehyde
(Formalin there is 431510009). highdicom's `SpecimenStaining(substances)` and
wsidicom's `Staining(substances)` take a list of substances in the same way
(https://raw.githubusercontent.com/ImagingDataCommons/highdicom/master/src/highdicom/content.py,
https://raw.githubusercontent.com/imi-bigpicture/wsidicom/main/wsidicom/metadata/sample.py).

## 4. Text forms for a code

- PS3.16 chapter 6 writes a coded concept as `(CV, CSD, "CM")` in its own
  tables
  (https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_6.html);
  that is documentation notation, and on the wire a code is always a Code
  Sequence item. No DICOM-defined compact string such as `SCT:12710003` was
  found (PS3.18 and PS3.19 not searched exhaustively, *to confirm*).
- FHIR's search token is `[system]|[code]`
  (https://hl7.org/fhir/R5/search.html#token), and PS3.16 Table 8-1 gives the
  system URIs: SCT is `http://snomed.info/sct`, DCM is
  `http://dicom.nema.org/resources/ontology/DCM`
  (https://dicom.nema.org/medical/dicom/current/output/chtml/part16/chapter_8.html).

## 5. Which scanners know the stain at scan time

From the vendor surveys of 2026-11-24 (`leica_aperio_hamamatsu_2026-11-24.md`,
`philips_3dhistech_roche_others_2026-11-24.md`):

- Olympus (Evident) VSI is the only brightfield format with a stain field:
  `Staining` [2059], beside `Specimen`, `Tissue` and `Preparation`, free text
  an operator enters at scan time. It is the laboratory's knowledge typed into
  the scanner, uncoded.
- Aperio's `Dye` names the fluorophore of each fluorescence channel (`DAPI`):
  a channel property of the optical path, not the histological stain.
- Philips iSyntax, 3DHistech MRXS, Roche/Ventana BIF, Hamamatsu NDPI, Leica SCN
  and the KFB format carry no stain. Roche label stock can print a stain or
  protocol code, which a scanner sees only as barcode or label pixels.
- No surveyed format records a fixative.

So the stain and the fixative are known to the laboratory information system,
which ordered the stain and fixed the tissue, and reach a scanner only when a
person or an interface copies them in.

## 6. How FHIR records them

FHIR R5 Specimen (https://hl7.org/fhir/R5/specimen.html,
https://hl7.org/fhir/R5/specimen-definitions.html; maturity 2, Trial Use) has
no stain or fixative element. Both are processing steps:

| Element | Card. | Type | Binding |
|---|---|---|---|
| `Specimen.processing` | 0..* | BackboneElement | |
| `Specimen.processing.description` | 0..1 | string | |
| `Specimen.processing.method` | 0..1 | CodeableConcept | Specimen Processing Method (http://hl7.org/fhir/ValueSet/specimen-processing-method), Example |
| `Specimen.processing.additive` | 0..* | Reference(Substance) | |
| `Specimen.processing.time[x]` | 0..1 | dateTime \| Period | its definition's example is the time a sample was fixed, or how long it was in formalin |

- **A stain:** a `processing` step whose `method` is a SNOMED CT staining
  procedure (127790008 "Staining"; the Example value set has no general
  staining code, and an Example binding allows one outside it) and whose
  `additive` references one `Substance` per dye, H&E being two.
- **A fixative:** a `processing` step whose `method` is 787378005 "Fixation of
  specimen (procedure)" (in the value set,
  https://hl7.org/fhir/R5/valueset-specimen-processing-method.html), with
  `additive` referencing the fixative `Substance` and `time[x]` its period.
- `Substance.code` is 1..1 CodeableReference(SubstanceDefinition), binding
  Example (https://hl7.org/fhir/R5/substance-definitions.html); a dye or a
  fixative is `Substance.code.concept.coding` = {`http://snomed.info/sct`,
  the CID 8112 or 8114 code}, with `Substance.instance` false.
- R5 removed `Specimen.container.additive[x]`, which in R4
  (https://hl7.org/fhir/R4/specimen-definitions.html) was 0..1 CodeableConcept
  \| Reference(Substance), "Examples: Formalin, Citrate, EDTA"; in R4 the
  processing step's code was `processing.procedure` instead of `method`.
- The German Medical Informatics Initiative's pathology module (FHIR R4) maps
  the staining process to `Specimen.processing.procedure` (SNOMED CT, under
  127790008) and the dyes to `Specimen.processing.additive` → Substance
  (https://www.medizininformatik-initiative.de/Kerndatensatz/KDS_Pathologie_Befund_EN/MIIIGModulePathologieBefund-Technicalimplementation-Terminologies.html).
  The HL7 anatomic pathology IG and IHE PaLM were not read (*to confirm*).

## 7. Conclusion for I2S

DICOM's own codes for both facts (CID 8112, CID 8114) are SNOMED CT, the same
codes FHIR's `Substance.code` carries, so moving them to the clinical metadata
stream loses nothing a DICOM converter needs: a converter writes TID 8003 and
TID 8001 row 10 from the FHIR `Specimen.processing` steps. Neither fact is
known to the scanner (section 5). Decided 2026-11-25 (Decision_17): both go
to FHIR, and `CODE` and `code_sets` are not built, since they had no other
user.
