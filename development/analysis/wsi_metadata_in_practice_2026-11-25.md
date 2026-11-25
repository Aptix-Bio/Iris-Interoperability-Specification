# WSI metadata in practice: what real files carry, and what I2S should add

Research date: 2026-11-25. Read-only; no repository was edited.

Legend for frequency: "always" = mandatory in the format; "usually" = present in most files from the named source; "sometimes" = present in some files or converters; "unmeasured" = no frequency data found. No real-file census was run, so frequency is qualitative.

## 0. What the .iris / IFE and I2S already hold (do not duplicate)

Local sources read: IFE `spec/ife_fields.json` and `spec/ife_constants.json`; I2S `spec/i2s_keys.json` and `spec/i2s_spec.adoc`.

IFE METADATA block (1.0 and 1.1):

| IFE field | Version | Meaning | Overlaps with |
|---|---|---|---|
| MICRONS_PIXEL (f32) | 1.0 | Normalized microns per pixel at layer scale 1 | DICOM PixelSpacing; OpenSlide openslide.mpp-x/-y |
| MAGNIFICATION (f32) | 1.0 | Normalized coefficient, layer scale to objective magnification | DICOM ObjectiveLensPower; openslide.objective-power |
| ICC_COLOR_OFFSET (ICC_PROFILE block) | 1.0 | ICC colour profile bytes | DICOM ICCProfile (0028,2000) |
| CLINICAL_OFFSET (CLINICAL_METADATA block) | 1.1 | Opaque clinical/identity stream, split out so it can be removed | Patient, request, interpretation |
| MICRONS_PLANE (f32) | 1.1 | Physical distance between adjacent focal planes; 0 = unknown | DICOM DistanceBetweenFocalPlanes (0048,0014) |
| Z_PLANES (u16, LAYER_EXTENT) | 1.1 | Max focal planes per tile in a layer | DICOM NumberOfFocalPlanes (0048,0013), partly |
| IMAGES block | 1.0 | Associated images (label, macro, thumbnail) | DICOM ImageType value 3 |
| ANNOTATIONS block | 1.0 | Annotations | n/a |

I2S keys already defined (`i2s_keys.json`, version 0.1): Manufacturer (0008,0070), ManufacturerModelName (0008,1090), DeviceSerialNumber (0018,1000), SoftwareVersions (0018,1020), UniqueDeviceIdentifier, AcquisitionDateTime (0008,002A). The I2S header also seeds the Digital Image Identifier with a PHI flag. I did not verify the tags for the existing keys against the DICOM standard in this run; they are taken from the I2S file.

IFE METADATA_I2S (ATTRIBUTES.FORMAT): the IFE spec says keys are DICOM keywords and that every pair is an acquisition fact that identifies no individual. Clinical and identifying facts belong in CLINICAL_METADATA. Source: `spec/ife_constants.json` (metadata_formats), `spec/ife_fields.json`.

Implication: MICRONS_PIXEL, MAGNIFICATION, ICC and focal-plane spacing are already first-class fields. If I2S adds PixelSpacing or ObjectiveLensPower as keys, they duplicate those fields. Decide whether I2S carries the raw DICOM value (source of truth) or stays out of the attribute vocabulary.

## 1. Optics and resolution

| Field | DICOM keyword / tag | OpenSlide / vendor name | Typical value | Units | Frequency | Patient-identifying? | Source |
|---|---|---|---|---|---|---|---|
| Pixel spacing | PixelSpacing (0028,0030) | openslide.mpp-x / mpp-y (from Pixel Spacing; Philips DICOM_PIXEL_SPACING; Aperio aperio.MPP; MIRAX MICROMETER_PER_PIXEL_X/Y; Ventana ventana.ScanRes; Leica TIFF XResolution; Sakura sakura.ResolutionMmPerPix) | 0.25, 0.5 | µm/px | always in DICOM WSI; "may be missing or inaccurate" in OpenSlide | No | https://openslide.org/docs/properties/ ; https://openslide.org/formats/dicom ; https://openslide.org/formats/aperio/ ; https://openslide.org/formats/mirax/ ; https://openslide.org/formats/philips/ ; https://openslide.org/formats/ventana/ ; https://openslide.org/formats/sakura/ |
| Objective lens power | ObjectiveLensPower (0048,0112), Optical Path module, Type 3 | openslide.objective-power (Aperio aperio.AppMag; Hamamatsu NDPI tag 65421 SourceLens; MIRAX GENERAL.OBJECTIVE_MAGNIFICATION; Ventana ventana.Magnification; Leica objective; Sakura NominalLensMagnification) | 20, 40 | x (dimensionless) | DICOM Type 3; OpenSlide "often inaccurate; sometimes missing" | No | https://openslide.org/formats/dicom ; https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.12.5.html ; https://openslide.org/formats/hamamatsu/ |
| Objective numerical aperture | ObjectiveLensNumericalAperture (0048,0113), Type 3 | leica.aperture (Leica numericalAperture) | 0.75 | unitless | Sometimes (Leica exposes it; not in OpenSlide's standard list) | No | https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.12.5.html ; https://openslide.org/formats/leica/ |
| Condenser lens power | CondenserLensPower (0048,0111), Type 3 | none | | x | Rare | No | C.8.12.5 (same as above) |
| Total pixel matrix size | TotalPixelMatrixColumns / Rows | derived from level dimensions | | px | always (structural) | No | Not verified in this run; derivable from IFE LAYER_EXTENTS |
| Bounds of scanned region | none standard in DICOM | openslide.bounds-x/-y/-width/-height | | px | "Not always present" | No | https://openslide.org/docs/properties/ |

Note on the DICOM tag for ObjectiveLensPower: an automated search suggested (0048,0004). The Optical Path module page gives (0048,0112). Use (0048,0112).

## 2. Focus and Z-stack

| Field | DICOM keyword / tag | Vendor name | Typical value | Units | Frequency | Patient-identifying? | Source |
|---|---|---|---|---|---|---|---|
| Imaged volume depth | ImagedVolumeDepth (0048,0003), Type 1C, required when ImageType value 3 = VOLUME, must not be 0 | none | 0 or depth of focal stack | µm | Required for VOLUME; converters often write 0 (wsidicomizer README) | No | https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.12.4.html ; https://github.com/cytomine/wsidicomizer |
| Imaged volume width/height | ImagedVolumeWidth (0048,0001), ImagedVolumeHeight (0048,0002) | none | | mm | Type 1C for VOLUME; converters often write 0 | No | same as above |
| Focus method | FocusMethod (0048,0011), Type 1 | none found | AUTO or MANUAL | enum | Type 1 in DICOM (so always present in conformant files) | No | https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.12.4.html |
| Extended depth of field | ExtendedDepthOfField (0048,0012), Type 1 | none | YES or NO | enum | Type 1 in DICOM | No | same |
| Number of focal planes (EDoF) | NumberOfFocalPlanes (0048,0013), Type 1C (required when EDoF = YES) | Hamamatsu NDPI: only focal plane 0 read; Leica and Philips: only plane 0 used | 1, 3, 7, 11 | count | Conditional | No | same; https://openslide.org/formats/leica/ |
| Distance between focal planes | DistanceBetweenFocalPlanes (0048,0014), Type 1C | none | e.g. 1.0 to 2.0 | µm | Conditional on EDoF | No | same. Duplicates IFE MICRONS_PLANE |
| Z offset of tile or plane | Z offset in slide coordinates (not fetched in this run; tag unverified) | Hamamatsu NDPI tag 65424 "Z offset/focus" (possibly nm, not documented; OpenSlide reads plane 0 only) | | µm or nm | Vendor-specific | No | https://openslide.org/formats/hamamatsu/ |
| Volumetric properties | VolumetricProperties (0008,9206), Type 1 | none | VOLUME, SAMPLED, DISTORTED | enum | Type 1 | No | C.8.12.4 |

## 3. Specimen and stain

| Field | DICOM keyword / tag | Vendor name | Typical value | Units | Frequency | Patient-identifying? | Source |
|---|---|---|---|---|---|---|---|
| Specimen description sequence | SpecimenDescriptionSequence (0040,0560), Type 1 | none | | | always in DICOM WSI | Container holds identifiers (see below) | https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.7.6.22.html |
| Specimen identifier | SpecimenIdentifier (0040,0551), Type 1 | Hamamatsu AuthCode (unverified), Leica barcode | lab accession plus slide number | text | always in DICOM WSI | Yes, usually, when it encodes an accession number. Check PS3.15 E.1-1 (not fetched in this run) | C.7.6.22 |
| Specimen UID | SpecimenUID (0040,0554), Type 1 | none | UID | UID | always | No (opaque UID) | C.7.6.22 |
| Container identifier | ContainerIdentifier (0040,0512), Type 1 | openslide.barcode (Philips, Leica, Hamamatsu barcode values) | slide barcode | text | usually when a barcode exists | Yes, usually, identifies a case | C.7.6.22; https://openslide.org/docs/properties/ |
| Specimen short description | SpecimenShortDescription (0040,0600), Type 3 | none | free text | text | sometimes | Possibly; free text | C.7.6.22 |
| Specimen type | SpecimenTypeCodeSequence (0040,059A), Type 3 (CID 8103) | none | coded | code | sometimes | No | C.7.6.22 |
| Primary anatomic structure | PrimaryAnatomicStructureSequence (tag not verified; CID 8134) | IDC column primaryAnatomicStructureModifier_CodeMeaning (e.g. "Neoplasm, Primary", "Normal") | coded (e.g. breast, liver) | code | Sometimes; IDC uses it | No direct identity, but clinical (diagnosis-related) | https://cdn.jsdelivr.net/npm/@saibolla/ada@0.1.3/skills/imaging-data-commons/references/digital_pathology_guide.md ; C.7.6.22 |
| Preparation steps (stain, fixative, embedding) | SpecimenPreparationSequence (0040,0610), Type 2; SpecimenPreparationStepContentItemSequence (0040,0612), Type 1; TID 8001 | IDC columns: staining_usingSubstance_CodeMeaning (e.g. hematoxylin), tissueFixative_CodeMeaning, embeddingMedium_CodeMeaning | "hematoxylin and eosin" as CID code | code | usually for stained slides; the IDC guide queries it as an array | No | C.7.6.22; IDC digital pathology guide (above) |
| Stain / illumination (brightfield) | IlluminatorTypeCodeSequence (0048,0100), Type 3; IlluminationTypeCodeSequence (0022,0016), Type 1 | none | e.g. brightfield | code | Type 1 in DICOM for illumination type | No | C.8.12.5 |
| Fluorescence channel | IlluminationWaveLength (0022,0055), Type 1C; IlluminationColorCodeSequence (0048,0108), Type 1C; OpticalPathIdentifier (0048,0106), Type 1; OpticalPathDescription (0048,0107), Type 3 | Used for multichannel (IF) slides | nm or colour code; channel name | nm / text | Conditional; relevant only to multichannel | No | C.8.12.5 |

Acquisition-level note: DICOM sm_index columns in IDC include ObjectiveLensPower and min_PixelSpacing_2sf, which indicates these are the fields IDC users actually filter on. Frequency per field is not reported in IDC docs.

## 4. Scan and device

| Field | DICOM keyword / tag | Vendor name | Typical value | Units | Frequency | Patient-identifying? | Source |
|---|---|---|---|---|---|---|---|
| Manufacturer, model, serial, software | Manufacturer, ManufacturerModelName, DeviceSerialNumber, SoftwareVersions (already in I2S) | Aperio ScanScope ID (unverified key name); Philips "Philips" Software tag; Leica device model/version; MIRAX; Ventana iScan attributes | | | usually | Serial number can be a device fingerprint; not patient identity | https://openslide.org/formats/leica/ ; https://openslide.org/formats/philips/ |
| Acquisition date and time | AcquisitionDateTime (already in I2S); TIFF DateTime (tiff.DateTime) | Aperio Date/Time (unverified); Leica creationDate | | | usually | Close to patient procedure dates; I2S flags this as an open question | https://openslide.org/docs/properties/ ; https://openslide.org/formats/leica/ |
| Acquisition device type | AcquisitionDeviceType (not fetched in this run) | none | | | Not verified | No | |
| Acquisition device processing description | AcquisitionDeviceProcessingDescription (0018,1400) (cited in the C.8.12.4 page) | none | free text | text | sometimes | No | https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_C.8.12.4.html |
| Scanner software / host | tiff.Software, tiff.HostComputer, tiff.Make, tiff.Model | | | | usually in TIFF-based vendors | Host name could identify a workstation | https://openslide.org/docs/properties/ |
| Focus / scan method | Aperio "Focus Offset", "StripeWidth", "Filtered" keys | Aperio ImageDescription key-value pairs | | | Not verified (see section 6) | No | Not verified |
| Comment | openslide.comment | Free text | | text | sometimes | Possibly | https://openslide.org/docs/properties/ |

## 5. Image and colour

| Field | DICOM keyword / tag | Vendor name | Typical value | Units | Frequency | Patient-identifying? | Source |
|---|---|---|---|---|---|---|---|
| ICC profile | ICCProfile (0028,2000), Type 1C; ColorSpace (0028,2002), Type 3 | openslide.icc-size; IFE ICC_PROFILE | sRGB profile bytes | bytes | Sometimes; required for non-MONOCHROME2 | No | C.8.12.5; https://openslide.org/docs/properties/ |
| Image type (flavour) | ImageType (0008,0008), Type 1; value 3 = VOLUME, LABEL, OVERVIEW, THUMBNAIL | Associated images label, macro, thumbnail (OpenSlide) | | enum | always | No | C.8.12.4; https://openslide.org/formats/dicom |
| Specimen label in image | SpecimenLabelInImage (0048,0010), Type 1 | | YES or NO | enum | always | No | C.8.12.4 |
| Lossy compression | LossyImageCompression (0028,2110), LossyImageCompressionRatio (0028,2112), LossyImageCompressionMethod (0028,2114) | none | YES, ratio, JPEG | | Standard Image Pixel module; not fetched in this run | No | Not verified in this run |
| Background colour | openslide.background-color | | RGB hex | | Not always present | No | https://openslide.org/docs/properties/ |
| Barcode | openslide.barcode | Philips PIM_DP_UFS_BARCODE; Leica barcode | | text | sometimes | Yes, often | https://openslide.org/formats/philips/ ; https://openslide.org/formats/leica/ |
| Quickhash | openslide.quickhash-1 | | hash | | always when OpenSlide opens the file | No | https://openslide.org/docs/properties/ |
| Vendor | openslide.vendor | | aperio, hamamatsu, ... | | always | No | https://openslide.org/docs/properties/ |

## 6. Vendor-specific fields (OpenSlide docs, as read)

- Aperio SVS: ImageDescription is "Aperio"-prefixed, equals-delimited key-value pairs stored as aperio.*. OpenSlide maps aperio.MPP to mpp-x/mpp-y and aperio.AppMag to objective-power. The page says OpenSlide uses no other keys. Keys named in the brief (ScanScope ID, Date, Time, Filtered, Focus Offset, StripeWidth) were not confirmed in this run; the OpenSlide page cites Aperio's own vendor PDF, which was not retrieved. Source: https://openslide.org/formats/aperio/
- Hamamatsu NDPI: tag 65421 SourceLens (objective power; -1 and -2 are special levels); 65422 and 65423 X and Y offset from slide centre; 65424 Z offset/focus; 65427 Reference; 65428 maybe AuthCode; mpp from XResolution/YResolution when ResolutionUnit is cm. Source: https://openslide.org/formats/hamamatsu/
- MIRAX Slidedat.ini: GENERAL.OBJECTIVE_MAGNIFICATION; LAYER_0_LEVEL_0_SECTION MICROMETER_PER_PIXEL_X/Y; barcode is the ScanDataLayer_SlideBarcode image. No focus or scan-date keys documented. Source: https://openslide.org/formats/mirax/
- Philips TIFF: DICOM-like XML in ImageDescription; DICOM_PIXEL_SPACING; PIM_DP_UFS_BARCODE. No Z, serial or ICC mapping documented. Source: https://openslide.org/formats/philips/
- Leica SCN: numericalAperture (leica.aperture), barcode, creationDate, device model and version, illuminationSource, objective. Focal plane 0 only. Source: https://openslide.org/formats/leica/
- Ventana BIF: iScan element attributes become ventana.*; ScanRes to mpp; Magnification to objective-power. Z, scan date and serial not documented. Source: https://openslide.org/formats/ventana/
- Sakura: SVSlideDataXPO and SVHRScanDataXPO fields: SlideId, Date, Description, DiagnosisCode, FocussingMethod, NominalLensMagnification, ResolutionMmPerPix, ScanId. Source: https://openslide.org/formats/sakura/

## 7. Consensus and converter guidance

- Herrmann MD, Clunie DA, Fedorov A et al., "Implementing the DICOM standard for digital pathology", J Pathol Inform 2018;9:37, DOI 10.4103/jpi.jpi_42_18. The paper implements 114 WSI IOD attributes: 93 required or conditionally required, 21 optional. The per-attribute list is in Supplementary Table 1, which was not reachable here. It does not give a minimal set or a de-identification list. Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC6236926
- wsidicomizer (cytomine / imi-bigpicture): merges metadata from the source file with user-supplied metadata. Known gap: slice thickness, focal plane thickness and imaged volume are written as 0. Source: https://github.com/cytomine/wsidicomizer
- Google wsi-to-dicom-converter (Apache-2.0, uses OpenSlide inputs): mapping of properties to DICOM not verified in this run. Source: https://github.com/GoogleCloudPlatform/wsi-to-dicom-converter
- OpenSlide 2023 mailing-list thread proposed inferring openslide.objective-power from DICOM ObjectiveLensPower and mpp from PixelSpacing. Source: https://lists.andrew.cmu.edu/pipermail/openslide-users/2023-May/001642.html
- IDC sm_index / sm_instance_index: the digital pathology guide names ObjectiveLensPower, min_PixelSpacing_2sf, staining_usingSubstance_CodeMeaning, embeddingMedium_CodeMeaning, tissueFixative_CodeMeaning, primaryAnatomicStructureModifier_CodeMeaning, ContainerIdentifier, SeriesInstanceUID. The full column list was not retrieved (idc-index column page returned no sm columns in this run; the page is a 404 or lacks them). Sources: https://cdn.jsdelivr.net/npm/@saibolla/ada@0.1.3/skills/imaging-data-commons/references/digital_pathology_guide.md ; https://idc-index.readthedocs.io/en/latest/indices_reference.html . Not verified: a full column census.
- highdicom: library exists (herrmannlab/highdicom). No WSI example code for these attributes was found in this run. Not verified beyond that.

## 8. Ranked list: fields most worth adding to I2S

Excludes fields already in IFE (PixelSpacing, ObjectiveLensPower, ICC, focal-plane spacing, Z plane count) unless I2S wants a raw DICOM copy. Excludes identity-bearing fields, which belong in CLINICAL_METADATA or need a PHI flag.

1. ObjectiveLensNumericalAperture (0048,0113), Type 3. Not in IFE; needed for resolution limits. Leica exposes it.
2. ImagedVolumeDepth (0048,0003), Type 1C, µm. Not in IFE; the Z extent of the focal stack. Converters often write 0, so treat 0 as "unknown" (see IFE MICRONS_PLANE convention).
3. FocusMethod (0048,0011), Type 1, AUTO or MANUAL. Not in IFE.
4. ExtendedDepthOfField (0048,0012), Type 1, YES or NO. Not in IFE; says whether pixels are a focus-stacked composite.
5. NumberOfFocalPlanes (0048,0013), Type 1C, for EDoF stacks. Partly in IFE Z_PLANES (per-tile maximum); the DICOM count is the acquired count and differs.
6. IlluminatorTypeCodeSequence (0048,0100) and IlluminationTypeCodeSequence (0022,0016), Type 1 for the latter. Not in IFE; brightfield vs fluorescence.
7. SpecimenPreparationSequence (0040,0610) and SpecimenPreparationStepContentItemSequence (0040,0612), Type 2 and 1. Stain, fixative and embedding; the field IDC filters on. Coded values; low identity risk.
8. PrimaryAnatomicStructureSequence (CID 8134; tag not verified in this run). Tissue type; IDC filters on it. Clinical-adjacent; consider CLINICAL_METADATA or a flag.
9. OpticalPathIdentifier (0048,0106) and OpticalPathDescription (0048,0107). Needed to name channels in multichannel and fluorescence slides.
10. IlluminationWaveLength (0022,0055) and IlluminationColorCodeSequence (0048,0108), conditional on the above. Fluorescence channel wavelength.
11. SpecimenTypeCodeSequence (0040,059A), Type 3, CID 8103. Specimen kind (tissue section, cytology, etc.).
12. SpecimenShortDescription (0040,0600), Type 3. Free text; review for identifying content before use.
13. VolumetricProperties (0008,9206), Type 1: VOLUME vs SAMPLED vs DISTORTED. Says whether pixels can be geometrically manipulated.
14. ImageType (0008,0008) value 3 (VOLUME, LABEL, OVERVIEW, THUMBNAIL). IFE IMAGES already encodes the associated-image roles, so this is likely redundant; include only if I2S wants the DICOM flavour on the main level.
15. LossyImageCompression (0028,2110), LossyImageCompressionRatio (0028,2112), LossyImageCompressionMethod (0028,2114). Compression quality; not verified in this run.

Not recommended for I2S: SpecimenIdentifier (0040,0551), ContainerIdentifier (0040,0512), barcode, AcquisitionDateTime (already present; PHI review is open), DeviceSerialNumber (already present). These are identifying or near-identifying and belong in CLINICAL_METADATA or need an explicit PHI flag in I2S.

## 9. Unverified or open items

- The DICOM tags for PixelSpacing (0028,0030), Pixel Measures and Z offset in slide coordinates were not fetched (the Pixel Measures page returned 404). Tag values for those are from general knowledge.
- Tag and CID for PrimaryAnatomicStructureSequence were not confirmed.
- Lossy compression tags (0028,2110-2114) were not fetched.
- Aperio keys ScanScope ID, Date, Time, Filtered, Focus Offset and StripeWidth were not verified against the Aperio vendor PDF.
- Frequency figures are qualitative. No census of real files was run; IDC's sm_index columns would give an actual count if queried in BigQuery.
- The DICOM PS3.15 Table E.1-1 de-identification actions for SpecimenIdentifier, ContainerIdentifier and PrimaryAnatomicStructure were not checked in this run.
- The I2S header says the scan time is an open question for the maintainer. This report did not resolve it.
