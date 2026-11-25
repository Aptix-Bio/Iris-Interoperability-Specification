# Are slide metadata fields "identifiers of a person"? What the sources say

Date read: 2026-11-24. Not legal advice; this reports what the texts say, where they disagree, and where they are silent. Items marked *(to confirm)* were not verified in a primary text.

Access notes. hhs.gov returned HTTP 403 to automated fetches, so the HHS OCR guidance was read from an Internet Archive snapshot of the same page (2024 capture). The page text matches the OCR guidance structure (Q 3.1-3.7). documents.cap.org did not resolve from this machine, so CAP PDFs were read from Internet Archive copies. EUR-Lex returned an empty body, so the GDPR text was read from an Internet Archive copy of the EUR-Lex HTML (CELEX 32016R0679). eCFR and dicom.nema.org were read directly.

## 1. HIPAA Privacy Rule

### 1.1 Safe Harbor list, 45 CFR 164.514(b)(2)(i)
Source: https://www.ecfr.gov/current/title-45/part-164/section-164.514 (read via eCFR versioner API, 2026-11-24).
- (C) "All elements of dates (except year)" for dates "directly related to an individual" (HHS page below gives the full clause: birth, admission, discharge, death dates, ages over 89).
- (H) "Medical record numbers"; (J) "Account numbers"; (M) "Device identifiers and serial numbers"; (R) "Any other unique identifying number, characteristic, or code".
- (b)(2)(ii): the covered entity must lack "actual knowledge" that the remaining information could identify an individual.
- Not enumerated: accession numbers, specimen/block/slide IDs, stain names, institution/lab names (geographic item (B) covers subdivisions smaller than a State, e.g. street, city, ZIP), scanner location as such. The CFR text is silent on them by name; they fall under (R) or the actual-knowledge clause only if they are unique to/linkable to the individual.

### 1.2 164.514(a), (c), (e)
- (a): de-identified means "no reasonable basis to believe" the information "can be used to identify an individual".
- (c) re-identification code: allowed if "not derived from or related to information about the individual" and "not otherwise capable of being translated so as to identify the individual"; and the covered entity does not use or disclose it "for any other purpose" nor disclose the re-identification mechanism. Source: same eCFR section.
- Limited data set, 164.514(e)(2): excludes direct identifiers including medical record numbers, account numbers, device identifiers and serial numbers; does NOT exclude dates, or town/city, State, ZIP. Use only for research, public health, health care operations, under a data use agreement (e)(3)(i)/(e)(4). Accession number is not listed. Source: eCFR 164.514(e).

### 1.3 HHS OCR guidance (Nov 26, 2012), "Guidance Regarding Methods for De-identification of PHI"
Source: https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html (Internet Archive capture of this URL, read 2026-11-24; direct fetch 403).
- Dates (Q "examples of dates"): elements "more specific than the year of an event" are not permitted; "January 1, 2009" may be reported only as "2009". Records contain "dates of service or other events".
- Dates (Q on test measures): dates from a laboratory report "are directly related to a specific individual" and are PHI; no element of such a date other than year may be reported under Safe Harbor.
- (R) catch-all: "any unique features that are not explicitly enumerated" but "could be used to identify a particular individual". Examples given: clinical trial record numbers (citing 65 FR 82462, 82712); an identifying code: a hash with no secret key "would be considered an identifying element"; barcodes: EMR and e-prescribing systems "assign and embed barcodes" that are "unique for each patient, or event in a patient's record" and so serve tracking; an identifying characteristic (occupation example).
- Codes: "a code or other means of record identification that is derived from PHI would have to be removed" under Safe Harbor; the 164.514(c) exception covers codes assigned by the covered entity that satisfy (c).
- Actual knowledge: "clear and direct knowledge" that remaining information could identify the individual.
- The guidance does not mention accession numbers or scanner/device identifiers by name, and does not define "device identifiers" (checked the guidance text for "accession" and "device"; only the regulation list contains "device identifiers"). *(to confirm: whether the 2000 preamble, 65 FR 82712, says what "device identifiers" means; the term predates FDA's UDI rule, 78 FR 58786, Sept 24, 2013, not verified.)*

### 1.4 Reading for each field (what the text supports)
- Scan date/time: a scan date of a clinical slide is a date of a health-care event on that patient's specimen. HHS says lab-report dates are "directly related to a specific individual". The sources do not address slide scan dates specifically. The MIDI report (see 5.2) says "Arguably, the date on which an imaging study was performed can be related to an individual." So: probably within (C) when attached to a clinical slide; year-only passes. Time of day is below year granularity.
- Accession number: not listed. CAP calls it the primary link from specimen, blocks and slides "to the patient" (see 5.1). Under (R) and HHS's barcode/code examples, a case-unique number assigned by the lab and tied to the patient record is a "unique identifying number" in the HHS sense. Whether it can stay under 164.514(c) depends on the number not being "derived from or related to information about the individual" (an S24-12345 style number encodes year and sequence only; it is not derived from patient data, but it is used for other purposes, e.g. on the report, so the (c) condition on non-use for other purposes is not met when it is also on the report). Reading is mine; the sources are silent on accession numbers specifically.
- Specimen/block/slide IDs and barcodes: same reasoning as accession (they usually embed it, CAP format S14-9999-A1-1). HHS names barcodes explicitly as potential (R) identifiers.
- Stain name: not an identifier by itself; no source lists it. CAP says stain/procedure is printed on the slide label next to the accession. MIDI lists "stains and dates" as label content to be handled. A stain name alone does not name or single out a person; combined with other fields it contributes to uniqueness.
- Scanner serial number: item (M) "Device identifiers and serial numbers" is in the list verbatim. Whether an instrument serial of a lab scanner (not an implant) is meant is unaddressed in the guidance. Literal text includes it. *(to confirm: intent of (M); regulatory history in the 2000 final rule preamble.)*
- Scanner UDI: the DI part names a model and labeler, the PI part (serial/lot) names an instance; see 4. Under (M) an instance PI serial is the literal case; a DI alone is a catalogue identifier shared by all units of a model.
- Institution/lab name: not enumerated. Geographic item (B) concerns address-level data (street, city, ZIP). Institution name might imply a city; the guidance does not say. *(to confirm)*
- Scanner location: if it is street address/city/ZIP below State level, (B) applies literally (only 3-digit ZIP with population condition, State allowed). Room/bench location inside a lab is not addressed.

## 2. GDPR (Regulation (EU) 2016/679)
Source: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679 (read via Internet Archive copy, 2026-11-24).
- Art. 4(1): personal data is information "relating to an identified or identifiable natural person"; identifiable includes by reference to "an identification number, location data" or factors specific to identity. An accession number is an identification number that points to a person through the lab's records.
- Art. 4(5) pseudonymisation: processing so data "can no longer be attributed to a specific data subject without the use of additional information", kept separately with technical and organisational measures.
- Recital 26: pseudonymised data attributable by additional information "should be considered to be information on an identifiable natural person"; test is "all the means reasonably likely to be used... by the controller or by another person", considering "costs" and "amount of time" and available technology; anonymous information is outside the Regulation.
- Recital 30: identifiers from devices (IP addresses, cookie IDs, RFID tags) "may be used to create profiles of the natural persons and identify them" when combined with other information.
- Art. 4(15): "data concerning health" is personal data revealing health status (a pathology slide metadata record tied to a patient is within this when identifiable); Art. 9 conditions apply. *(Art. 9 text not fetched; to confirm.)*
- Case law, CJEU C-413/23 P, EDPS v SRB, judgment of 4 September 2025 (ECLI:EU:C:2025:645). Only secondary summaries read (A&O Shearman, Goodwin, Clifford Chance, Jones Day via search results); primary page fetch returned empty. Reported holding: pseudonymised data is not always personal data for every recipient; identifiability is assessed from the recipient's means, while the controller who holds the key still processes personal data. *(to confirm against the judgment text, https://eur-lex.europa.eu/case/EN/C_413_23_P)*
- EDPB Guidelines 01/2025 on Pseudonymisation (version for public consultation adopted 16 Jan 2025; final status unconfirmed): pseudonymised data attributable with additional information remains personal data. https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf
- Application to fields: to the lab holding the accession-to-patient table, an accession number is personal data (pseudonym). To a recipient without that table and without reasonably likely means to obtain it, the SRB reading may allow treating it as not personal for that recipient; the EDPB draft takes the stricter view. Date, scanner serial, institution, stain: GDPR has no field list; they are personal data only if, alone or combined, they make the person identifiable by reasonably likely means. Combination risk is documented in the literature (5.3): case ID removed, acquisition date + scanner serial can re-identify.

## 3. DICOM PS3.15 Annex E (2026e), Basic Application Level Confidentiality Profile
Sources: https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html (Table E.1-1) and sect_E.3.6 / E.3.8 / E.3.9 / E.3.11 pages, same site; read 2026-11-24.
Action codes: D replace with dummy, Z replace with zero-length, X remove, K keep, C clean, U replace UID. "X/Z/D" means remove, or zero, or dummy as the attribute type permits.

| Attribute | Tag | Basic profile | Options that retain |
|---|---|---|---|
| Accession Number | (0008,0050) | Z | none |
| Container Identifier | (0040,0512) | D | none |
| Specimen Identifier | (0040,0551) | D | none |
| Barcode Value | (2200,0005) | X/Z | none |
| Study ID | (0020,0010) | Z | none |
| Acquisition DateTime | (0008,002A) | X/Z/D | K with Retain Long. Full Dates; C with Modified Dates |
| Acquisition Date / Time | (0008,0022)/(0008,0032) | X/Z | K full dates; C modified dates |
| Study Date / Time | (0008,0020)/(0008,0030) | Z | K full dates; C modified dates |
| Content Date | (0008,0023) | Z/D | K / C as above |
| Series Date | (0008,0021) | X/D | K / C |
| Device Serial Number | (0018,1000) | X/Z/D | K with Retain Device Identity |
| Unique Device Identifier | (0018,1009) | X | K with Retain Device Identity |
| UDI Sequence | (0018,100A) | X | K with Retain Device Identity |
| Device UID | (0018,1002) | U | K with Retain UIDs or Retain Device Identity |
| Station Name | (0008,1010) | X/Z/D | K with Retain Device Identity |
| Institution Name | (0008,0080) | X/Z/D | K with Retain Institution Identity |
| Institutional Department Name | (0008,1040) | X | K with Retain Institution Identity |

Notes:
- Stain names are not a distinct row. Stain/specimen descriptions live in Specimen Description / Specimen Preparation sequences and descriptor text; the Clean Descriptors option (E.3.5) addresses free text. Row for Specimen Short/Detailed Description and Specimen Preparation Sequence not extracted. *(to confirm in PS3.3 Table C.7.6.22 and Table E.1-1)*
- Manufacturer and Manufacturer's Model Name were not found in the Table E.1-1 rows extracted; the profile therefore does not list them for removal. *(to confirm by full table search)* MIDI says it is common practice to keep manufacturer and model but not serial number (5.2).
- E.3.6 (Retain Longitudinal Temporal Information, two mutually exclusive options): dates and times "are recognized as having a potential for leakage of identity because they constrain the number of possible individuals", "though only if there is access to other information about the individuals concerned to match it against".
- E.3.8 (Retain Device Identity) and E.3.11 (Retain Institution Identity) use the same rationale for devices and institutions: a "potential for leakage of identity because it may constrain the number of possible individuals", only with other data to match.
- E.3.9 (Retain UIDs) note: a DICOM UID "is not the same as a unique identifier of an individual, such as would be proscribed by some privacy regulations."
- PS3.15 states the profiles do not replace a de-identification process, which includes interpreting the applicable regulations.
- Reading: DICOM treats every field in the question as removable-by-default (X/Z/D), with scan time, device identity and institution each retainable by an explicit named option. Accession, container, specimen identifier and barcode have no retain option in the basic profile table; the encrypted-attributes mechanism (E.1.1) is DICOM's way to keep recoverability.

## 4. FDA UDI
Sources: eCFR 21 CFR 830.3 https://www.ecfr.gov/current/title-21/part-830/section-830.3 and 801.20 https://www.ecfr.gov/current/title-21/part-801/section-801.20 (read 2026-11-24); FDA GUDID page https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system/global-unique-device-identification-database-gudid (via search result summary; page not fetched directly *(to confirm)*).
- 830.3: UDI is "an identifier that adequately identifies a device through its distribution and use". Device identifier (DI) is "a mandatory, fixed portion of a UDI" that identifies the labeler and the specific version or model. Production identifier (PI) is "a conditional, variable portion of a UDI" that identifies lot/batch, serial number, expiration date, manufacturing date (and a distinct code for certain HCT/Ps).
- So: DI = model level, shared by every unit of that model; PI with serial = instance level. GUDID stores only DI plus flags for which PI types appear on the label; PI values (serial, lot) are not in GUDID (FDA/NLM pages, summary read).
- 801.20: requires a UDI on the device label and package. Nothing in 801.20 or 830.3 concerns patients; the UDI regime is about devices through distribution and use. FDA's regulation says nothing about whether a UDI identifies a person; the identification question is HIPAA's (M) and GDPR's reasonable-means test, not FDA's.
- Whether a given whole-slide scanner carries a UDI with serial in the PI depends on the vendor's labeling *(to confirm per product in AccessGUDID: https://accessgudid.nlm.nih.gov)*.

## 5. Pathology and imaging guidance
### 5.1 CAP
- Uniform Labeling of Blocks and Slides in Surgical Pathology (Brown et al., Arch Pathol Lab Med 2015;139:1515-24; guideline now marked inactive), https://documents.cap.org/documents/uniform-labeling-manuscript.pdf (Internet Archive copy read). Says the accession designation (e.g. S14-9999) is "the primary means of unambiguously linking" specimen, blocks and slides to the patient; recommends case type, year, unique number; slide IDs follow specimen and block IDs (S14-9999-A1-1); stain/procedure follows on the slide; two identifiers per block/slide, the second can be patient name, MRN, date of birth or a computer-generated barcode.
- Practical Tips to Assist Implementation of Whole Slide Imaging (CAP, 2025-10-01), https://documents.cap.org/documents/Practical-Tips-to-Assist-Implementation-of-Whole-Slide-Imaging-2025_10_01.pdf (Internet Archive copy read). Macro images "will typically include the slide label" with patient name, accession number, barcode and stain details; recommends 2D barcodes carrying accession number etc. for automatic archiving. It is a workflow document; no de-identification rule found in it.
- No CAP de-identification guidance for WSI was found. Searched CAP document library titles via web search only; the site's own search was not usable. *(to confirm)*

### 5.2 MIDI Task Group report (Clunie et al., 2025-02-07), https://arxiv.org/pdf/2303.10473
Not a regulator, but the most detailed public WSI statement found.
- Section 1.20.7.1.1: slide label may contain "accession, procedure (including stains and dates)"; scanners may OCR the label and write it to metadata and to file and folder names; if images are tracked by pseudonymized metadata "the label image can generally be completely discarded"; retained barcodes must be decoded and checked; new labels with pseudonymized identifiers can be synthesized.
- Dates: "Arguably, the date on which an imaging study was performed can be related to an individual and should be replaced." DICOM default removes all dates and times, with options to retain longitudinal information.
- Device/institution: default removes "identifiers and characteristics of the institution and the imaging device" as potential indirect identifiers; the public availability of device databases that match serial number to institutions "is only a theoretical concern at present"; common practice is to retain manufacturer and model but not serial number.
- Hashing: DICOM discourages unencrypted hashes ("trivial dictionary based attacks"; PS3.15 E.1.1); MIDI notes a keyed (salted) hash must have its key persisted to be reproducible, and a mapping table makes it reversible pseudonymization.
- HIPAA (report text on UID handling): "(R)" is "generally interpreted to refer to unique identifiers of the patient per se". This is MIDI's interpretation, not HHS's.

### 5.3 Bisson et al., Anonymization of Whole Slide Images in Histopathology for Research and Education (preprint, DIGITAL HEALTH), https://arxiv.org/pdf/2211.06103
- If the case ID is deleted, "the combination of image data, acquisition date and a scanner's serial number can make re-identification possible". Its Level III (label removed) is said to meet GDPR requirements; Level IV additionally removes scanner serial numbers, acquisition dates and times, operating-system user names, because they "can reveal a unique constellation" traceable if clinical systems are accessible. Author claims, not law.

### 5.4 Digital Pathology Association
No DPA primary guidance on WSI de-identification was found. *(to confirm; search found none)*

## 6. Where the sources agree, disagree, or are silent
- Agree: dates of clinical events below year, device serial numbers, and codes that point to a patient are treated as identifiers or indirect identifiers by HIPAA text (C, M, R), DICOM default profile, and the WSI literature.
- Differ on strength: HIPAA lists date elements and device serials as per se removable under Safe Harbor; DICOM and GDPR frame them as linkage risk ("only if there is access to other information"); MIDI calls the serial-to-institution lookup "theoretical".
- Silent: HHS and the CFR do not name accession numbers, stain names, scan dates of slides, scanner location inside a lab, or institution names. FDA is silent on patients. No regulator addresses scanner UDI.
- Disagree on pseudonyms under GDPR: EDPB draft keeps pseudonymised data personal; CJEU in SRB (as summarized) allows recipient-relative assessment.
- Consequence of a separate clinical stream: under both HIPAA and GDPR the accession number's identifying power comes from the linkage table (the lab's LIS or the FHIR stream). Splitting streams creates a pseudonym situation (GDPR Art. 4(5)); it does not by itself create de-identified data under HIPAA Safe Harbor, since Safe Harbor tests the data set for listed identifiers and codes derived from or relating to the individual, not who holds the key.

## 7. Design options this leaves (not a recommendation)
1. Accession number only in the clinical (HL7/FHIR) stream; I2S carries no case-level key. Removes the strongest linkage field; I2S then carries a slide-local random UID. Matches the DICOM default (Z) and MIDI label advice.
2. Accession in I2S, with I2S declared limited-data/PHI-bearing: governed as PHI or personal data for the lab; Safe Harbor not claimed; limited data set (164.514(e)) route covers dates and city/ZIP but still excludes device serials and MRN-type numbers and needs a data use agreement.
3. Random per-slide pseudonym in I2S, lookup table held only by the lab: fits 164.514(c) if not derived from patient data and the mapping is not disclosed; and GDPR Art. 4(5). Avoid a plain hash of the accession (HHS: an unkeyed hash is an identifying code; DICOM warns of dictionary attacks). A keyed hash keeps reproducibility but the key must be kept and the result remains reversible by the key holder (MIDI).
4. Dates: year only (passes HIPAA (C) text); or full date without time (still below year, so not Safe Harbor); or date shift preserving intervals (DICOM "Modified Dates" option C, an Expert Determination style approach, not Safe Harbor); or full dates and time flagged as retained (DICOM K via Retain Longitudinal Temporal Information Full Dates).
5. Scanner: model-level DI plus manufacturer and model in I2S, instance serial/PI omitted or optional (MIDI says manufacturer/model retention is common practice and serial is not; DICOM Retain Device Identity option exists for instance identity; HIPAA (M) literally lists serials; DI is a model code shared by every unit). If instance identity is needed for QC, mark it as an optional field outside the default profile.
6. Institution name and scanner location: keep as optional/organizational fields, or coarse (State or country); DICOM and MIDI treat them as indirect identifiers only in combination; HIPAA lists no institution name but does list sub-State geography.
7. Stain names: nothing in the sources treats them as identifiers; keep, in a controlled vocabulary rather than free text (DICOM Clean Descriptors rationale: free text leaks identities).
8. Label/macro images, barcode payloads and filenames sit outside the listed fields but are the main practical leak in the WSI sources (MIDI, Bisson); any I2S rule on them should be explicit.

## 8. Source list (all read 2026-11-24)
- https://www.ecfr.gov/current/title-45/part-164/section-164.514
- https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html (archive copy)
- https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32016R0679 (archive copy)
- https://eur-lex.europa.eu/case/EN/C_413_23_P (not read directly; secondary summaries only)
- https://www.edpb.europa.eu/system/files/2025-01/edpb_guidelines_202501_pseudonymisation_en.pdf (via search summary)
- https://dicom.nema.org/medical/dicom/current/output/chtml/part15/chapter_E.html and sect_E.3.6, E.3.8, E.3.9, E.3.11
- https://www.ecfr.gov/current/title-21/part-830/section-830.3 ; https://www.ecfr.gov/current/title-21/part-801/section-801.20
- https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system/global-unique-device-identification-database-gudid (search summary)
- https://documents.cap.org/documents/uniform-labeling-manuscript.pdf ; https://documents.cap.org/documents/Practical-Tips-to-Assist-Implementation-of-Whole-Slide-Imaging-2025_10_01.pdf (archive copies)
- https://arxiv.org/pdf/2303.10473 (MIDI) ; https://arxiv.org/pdf/2211.06103 (Bisson et al.)
