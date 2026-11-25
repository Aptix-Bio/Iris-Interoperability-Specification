# I2S research: scan-time metadata in Philips, 3DHistech, Roche/Ventana, Zeiss, Olympus/Evident, Grundium, Motic, KFBio, Sakura slide files

Date read for all sources: 2026-11-24. Read-only research; no slide files downloaded. (One vendor PDF, the Roche BIF whitepaper, was fetched and its text extracted locally; it is documentation, not a slide.)

Class legend: **SLIDE** = indelible characteristic of the slide or its scan; **PATIENT** = identifies/describes a person; **AMBIGUOUS** = depends on how the lab uses the field (explained).
All example values are invented. "OS prop" = OpenSlide 4.x property name; "BF key" = Bio-Formats metadata key.
Items marked *(to confirm)* were not verified from a primary source or a real file.

## 0. Cross-vendor summary

| Format | Container | Where metadata lives | OpenSlide reads? | Bio-Formats reads? | Confidence in field list |
|---|---|---|---|---|---|
| Philips iSyntax (.isyntax) | proprietary, XML header + wavelet codeblocks | XML (DataObject/Attribute, DICOM-named) in file header | NO | NO (3rd-party: Philips Pathology SDK, libisyntax, pyisyntax, isyntax2raw) | High (libisyntax source + Glencoe isyntax2raw + 3rd-party schema) |
| Philips TIFF (.tiff, "DP v1.1") | tiled BigTIFF | XML in ImageDescription of IFD 0 (+ Software tag) | YES (`philips`) | No dedicated reader | Medium-high for structure, medium for the full key list (see 1.4) |
| 3DHistech MRXS | folder: .mrxs + Slidedat.ini + Index.dat + Data*.dat | Slidedat.ini (INI), plus XML blobs in data files | YES (`mirax`) | No dedicated MIRAX reader in list inspected (3DHistech TissueFAXS reader is a different product) *(to confirm)* | High for the INI keys seen in one real v2.2 sample; others *(to confirm)* |
| Roche/Ventana BIF | BigTIFF | XMP tag 0x02BC (XML) in IFD 0/1/2, plus Software, DateTime, ImageDescription, ICC tags | YES (`ventana`) | YES (VentanaReader) | High for DP 200 (Roche whitepaper); iScan Coreo/HT *(to confirm)* |
| Zeiss CZI (Axioscan) | ZISRAW segments | XML (ImageDocument/Metadata) in ZISRAWMETADATA + Label/SlidePreview attachments | YES (`zeiss`, 4.x) | YES (ZeissCZIReader) | Medium (spec is confidential; field names from Bio-Formats + OpenSlide source) |
| Olympus/Evident VSI/ETS | TIFF-like .vsi + _folder_/stack*/frame_t.ets | proprietary tag tree in VSI | NO | YES (CellSensReader) | Medium (tag IDs from Bio-Formats source) |
| Grundium Ocus | TIFF/SVS (also SZI, DICOM) | *(to confirm)* | Probably via aperio/generic-tiff *(to confirm)* | generic TIFF *(to confirm)* | Low |
| Motic | multi-file MDS (per Pathomation) | *(unknown)* | NO | NO *(to confirm)* | None |
| KFBio KFB / KFBF | single binary file | fixed binary header | NO (OpenSlide maintainers said unsupported, May 2024) | NO | Medium (header layout from a Rust third-party parser) |
| Sakura SVSlide (.svslide) | SQLite 3 (XPO ORM) | SQL tables | YES (`sakura`) | NO | High (OpenSlide source) |

---

## 1. Philips (IntelliSite Ultra Fast Scanner, SG300 / SG60 / SG20 "UFS", and Philips TIFF export)

### 1.1 Where metadata lives
* **iSyntax**: a header containing an XML document (root `DataObject`, children `Attribute`/`Array`/`DataObject`; each `Attribute` has a `Name`, optionally `Group`/`Element`/`PMSVR` attributes encoding a DICOM-style group+element pair). libisyntax maps (group, element) numbers to names; the names are the same DICOM-derived identifiers used in the TIFF export. Philips SDK (PixelEngine) exposes the same values as properties (v1: `DICOM_*` upper-case names; v2: snake_case).
  Evidence: libisyntax `src/isyntax/isyntax.c` (switch on group/element with the names in comments), Glencoe `isyntax2raw/__init__.py` (SDK v1 and v2 property names).
  URLs: https://github.com/amspath/libisyntax/blob/HEAD/src/isyntax/isyntax.c ; https://github.com/glencoesoftware/isyntax2raw/blob/HEAD/isyntax2raw/__init__.py
* **Philips TIFF**: IFD 0 `ImageDescription` holds an XML doc, root `DataObject ObjectType="DPUfsImport"`. Detected when TIFF `Software` starts with "Philips" (tifffile: `Philips DP`...). Children: `Attribute Name="..."`, `Attribute Name="PIM_DP_SCANNED_IMAGES"` -> `Array/DataObject ObjectType="DPScannedImage"` (one per WSI/LABELIMAGE/MACROIMAGE, discriminated by `PIM_DP_IMAGE_TYPE`), and per-level `PIIM_PIXEL_DATA_REPRESENTATION_SEQUENCE` -> `DataObject ObjectType="PixelDataRepresentation"`. Label and macro are Base64 JPEG in `PIM_DP_IMAGE_DATA` or stripped IFDs whose ImageDescription begins "Label"/"Macro".
  URLs: https://openslide.org/formats/philips/ ; https://github.com/openslide/openslide/blob/main/src/openslide-vendor-philips-tiff.c ; tifffile `series_philips`/`philips_metadata` https://github.com/cgohlke/tifffile
* OpenSlide naming: every leaf `Attribute` becomes `philips.<Name>`; per-level items become `philips.PIIM_PIXEL_DATA_REPRESENTATION_SEQUENCE[<i>].<Name>`... precisely `philips.<seqname>.PixelDataRepresentation[i]`-style (code: `"%s.%s[%d]"` with prefix and name; *(exact string to confirm on a real file)*). Only the first WSI `DPScannedImage` is walked. OpenSlide removes `tiff.ImageDescription` and `openslide.comment` from the property table.

### 1.2 Field table (iSyntax header and Philips TIFF DPUfsImport)
Key = exact `Attribute Name`. DICOM tag column is from libisyntax group/element numbers (DICOM standard attributes are standard tags; `101D`/`301D` are Philips private groups).

| Vendor key | DICOM / private tag | Meaning | Format / invented example | Written by | OS prop (TIFF only) / SDK name | Class |
|---|---|---|---|---|---|---|
| `DICOM_ACQUISITION_DATETIME` | (0008,002A) | Scan start | iSyntax: `"20210101103030.000000"`; newer files ISO 8601 `2021-01-01T10:30:30` (Glencoe comment); TIFF: same string | UFS scanners, all versions | `philips.DICOM_ACQUISITION_DATETIME`; SDK v1 `DICOM_ACQUISITION_DATETIME`, v2 `acquisition_datetime` | AMBIGUOUS: date+time of a scan is on the physical-slide chain but can re-identify with an audit log; date-only is low risk |
| `DICOM_MANUFACTURER` | (0008,0070) | Maker | `PHILIPS` | all | `philips.DICOM_MANUFACTURER`; v2 `manufacturer` | SLIDE |
| `DICOM_MANUFACTURERS_MODEL_NAME` | (0008,1090) | Model | `UFS Scanner` (libisyntax comment) | all | `philips.DICOM_MANUFACTURERS_MODEL_NAME`; v2 `model_name` | SLIDE |
| `DICOM_DEVICE_SERIAL_NUMBER` | (0018,1000) | Scanner serial | `FMT0123` ("FMT"+4 digits) | all | `philips.DICOM_DEVICE_SERIAL_NUMBER`; v2 `device_serial_number` | SLIDE |
| `DICOM_SOFTWARE_VERSIONS` | (0018,1020) | Quoted list: scanner software, firmware/build | `"1.8.6614" "20180906_R51"` | all | `philips.DICOM_SOFTWARE_VERSIONS`; v2 `software_versions` | SLIDE |
| `DICOM_DATE_OF_LAST_CALIBRATION` | (0018,1200) | Calibration date | `"20210101"` (quoted) | all | `philips.DICOM_DATE_OF_LAST_CALIBRATION`; v2 `date_of_last_calibration` | SLIDE |
| `DICOM_TIME_OF_LAST_CALIBRATION` | (0018,1201) | Calibration time | `"100730"` | all | same pattern; v2 `time_of_last_calibration` | SLIDE |
| `PIIM_DP_SCANNER_CALIBRATION_STATUS` | private (101D,100A) | Scanner calibration state | `OK` / `NOT OK` | newer SDK/UFS | `philips.PIIM_DP_SCANNER_CALIBRATION_STATUS` *(TIFF presence to confirm)*; v2 `scanner_calibration_status` | SLIDE |
| `PIIM_DP_SCANNER_RACK_NUMBER` | private (101D,1007) | Rack in the loader | `3` (range 1..15) | UFS | v2 `scanner_rack_number` | SLIDE (rack/slot are scan-time location; the user wants these) |
| `PIIM_DP_SCANNER_SLOT_NUMBER` | private (101D,1008) | Slot in rack | `7` (1..15) | UFS | v2 `scanner_slot_number` | SLIDE |
| `PIIM_DP_SCANNER_OPERATOR_ID` | private (101D,1009) | Operator id | `<Operator ID>` free string | UFS | v2 `scanner_operator_id` | AMBIGUOUS: identifies a staff member (person), not the patient; treat as PERSONNEL/privacy-sensitive, exclude from the indelible slide set or hash |
| `PIM_DP_SCANNER_RACK_PRIORITY` | private (301D,1010) | Rack priority | u16 e.g. `1` | UFS | v2 `scanner_rack_priority` | SLIDE (operational; low value) |
| `PIM_DP_UFS_INTERFACE_VERSION` | (301D,1001) | Data-model version | `5.0` (v1 iSyntax) or `100.5` (v2) | all | `philips.PIM_DP_UFS_INTERFACE_VERSION`; v2 `isyntax_file_version` | SLIDE |
| `PIM_DP_UFS_BARCODE` | (301D,1002) | **Slide barcode, Base64-encoded** | `SC5SMDAxMTc5LlAuQS4z` style; decodes to e.g. `H.22.0001179.P.A.3` | all (empty if no barcode) | `philips.PIM_DP_UFS_BARCODE` (raw Base64); OpenSlide decodes to `openslide.barcode`; v1 SDK `BARCODE`, v2 `barcode` | **AMBIGUOUS (high risk)**: lab-defined content; commonly accession/case/part/block/level; a third-party deid schema (TileBio) explicitly splits it into case_id/block/level and keeps it only in the secure map file |
| `PIM_DP_SCANNED_IMAGES` | (301D,1003) | Container for DPScannedImage objects | - | all | walked by OpenSlide | - |
| `PIM_DP_IMAGE_TYPE` | (301D,1004) | `WSI` / `LABELIMAGE` / `MACROIMAGE` | `WSI` | all | `philips.PIM_DP_IMAGE_TYPE`; v2 `image_type` | SLIDE (structure) |
| `PIM_DP_IMAGE_DATA` | (301D,1005) | Base64 JPEG of label/macro | binary | all | not a property (large) | **leaks**: label contains printed barcode/text |
| `DICOM_DERIVATION_DESCRIPTION` | (0008,2111) | Compression/encoder recipe | `PHILIPS UFS V1.8 \| Quality=3 \| DWT=1 \| Compressor=16` (libisyntax format string `PHILIPS UFS V%s \| Quality=%d \| DWT=%d \| Compressor=%d`); also holds `levels=...,sourceFilename=...` in TIFF (OpenSlide parses first value after `levels=` as objective power 1..200) | all | `philips.DICOM_DERIVATION_DESCRIPTION`; v2 `derivation_description` | SLIDE, **but** contains `sourceFilename` in the TIFF export: filename leak (see section 9) |
| `DICOM_LOSSY_IMAGE_COMPRESSION` | (0028,2110) | Lossy flag | `01` | all | `philips.DICOM_LOSSY_IMAGE_COMPRESSION` | SLIDE |
| `DICOM_LOSSY_IMAGE_COMPRESSION_METHOD` | (0028,2114) | | `"PHILIPS_DP_1_0"` | all | `philips.DICOM_LOSSY_IMAGE_COMPRESSION_METHOD`; v2 `lossy_image_compression_method` | SLIDE |
| `DICOM_LOSSY_IMAGE_COMPRESSION_RATIO` | (0028,2112) | | `"20"` | all | `philips.DICOM_LOSSY_IMAGE_COMPRESSION_RATIO`; v2 `lossy_image_compression_ratio` | SLIDE |
| `DICOM_SAMPLES_PER_PIXEL`, `DICOM_BITS_ALLOCATED`, `DICOM_BITS_STORED`, `DICOM_HIGH_BIT`, `DICOM_PIXEL_REPRESENTATION` | (0028,0002)/(0100)/(0101)/(0102)/(0103) | Pixel format | `3`, `8`, `8`, `7`, `0` | all | `philips.DICOM_*` | SLIDE |
| `DICOM_ICCPROFILE` | (0028,2000) | Embedded ICC profile (large; libisyntax skips) | bytes/Base64 | all | not exposed in props (TIFF: not in OpenSlide table by name) | SLIDE |
| `DICOM_PIXEL_SPACING` | (0028,0030) | mm per pixel, `"row col"` per level | `"0.00025" "0.00025"` | TIFF per PixelDataRepresentation; iSyntax via `UFS_IMAGE_DIMENSION_SCALE_FACTOR` | `philips.PIIM_PIXEL_DATA_REPRESENTATION_SEQUENCE...DICOM_PIXEL_SPACING`; mpp-x = 1000*[1], mpp-y = 1000*[0] | SLIDE |
| `DP_COLOR_MANAGEMENT` (object) | private | Container for ICC/colour settings | - | all | - | SLIDE |
| `DP_IMAGE_POST_PROCESSING` (object): `DP_SHARPNESS_GAIN_RGB24`, `DP_CLAHE_CLIP_LIMIT_Y16`, `DP_CLAHE_NR_BINS_Y16`, `DP_CLAHE_CONTEXT_DIMENSION_Y16` | private (301D,1013-1018) | Display post-processing | ints/floats | all | `philips.DP_*` | SLIDE (image-processing provenance) |
| `DP_WAVELET_QUANTIZER`, `DP_WAVELET_DEADZONE`, `DP_WAVELET_QUANTIZER_SETTINGS_PER_COLOR`, `..._PER_LEVEL` | private (301D,1019-101C) | Wavelet codec parameters | ints | all | `philips.DP_*` | SLIDE |
| `UFS_IMAGE_DIMENSION_NAME/TYPE/UNIT/SCALE_FACTOR/DISCRETE_VALUES_STRING` | private (301D,2004-2008) | Dimension axes (x, y, colour `"Y" "Co" "Cg"`), unit, scale | `"MicroMeter"`, `0.25` | iSyntax | v2 `view.dimension_*` | SLIDE |
| `UFS_IMAGE_BLOCK_COMPRESSION_METHOD`, `UFS_IMAGE_NUMBER_OF_BLOCKS`, `UFS_IMAGE_BLOCK_HEADERS`, ..., `UFS_IMAGE_VALID_DATA_ENVELOPES`, `UFS_IMAGE_OPP_EXTREME_VERTICES` | private (301D,200x) | Codec/tile structure and valid-region polygon | ints | iSyntax | - | SLIDE (structure, not I2S core) |

Not present in the iSyntax header (negative finding from libisyntax switch-statement and the third-party extractor): **no stain, no specimen/organ, no objective power attribute** (objective power is only recoverable from `DICOM_DERIVATION_DESCRIPTION` `levels=` in TIFF export, per OpenSlide), no focus settings, no patient name/ID. Scanner mode (ScanFactor 20x/40x) is implicit in pixel spacing. *(Fields in Philips IMS database, such as patient/case, are not in the file.)*

### 1.3 DICOM tags that appear (standard attributes only)
(0008,002A) Acquisition DateTime; (0008,0070) Manufacturer; (0008,1090) Manufacturer's Model Name; (0008,2111) Derivation Description; (0018,1000) Device Serial Number; (0018,1020) Software Versions; (0018,1200) Date of Last Calibration; (0018,1201) Time of Last Calibration; (0028,0002) Samples per Pixel; (0028,0030) Pixel Spacing; (0028,0100) Bits Allocated; (0028,0101) Bits Stored; (0028,0102) High Bit; (0028,0103) Pixel Representation; (0028,2000) ICC Profile; (0028,2110) Lossy Image Compression; (0028,2112) Lossy Image Compression Ratio; (0028,2114) Lossy Image Compression Method.
**None of the patient-module tags (0010,xxxx), Study/Accession (0008,0050) or Specimen (0040,0512 etc.) are named in libisyntax or OpenSlide's Philips code.** Philips' separate DICOM WSI export (Philips DICOM Conformance Statements) does carry patient and specimen modules; see section 9.

### 1.4 Open points
* Whether the Philips TIFF exporter writes `PIIM_DP_SCANNER_*`/operator/rack/slot attributes: same data model, but no real TIFF dump was found. *(to confirm)* with `openslide-show-properties` on the OpenSlide Philips-TIFF test file.
* Whether the iSyntax file name defaults to the barcode: *(to confirm)*; Philips IMS typically names files by its own scheme.
* Philips SDK documentation proper (Philips Pathology SDK / PixelEngine) is not public; v2 property list taken from Glencoe's code.

---

## 2. 3DHistech (Pannoramic SCAN / SCAN II / DESK / MIDI / 250 Flash), MRXS

### 2.1 Where metadata lives
Folder next to `<name>.mrxs`: `Slidedat.ini` (INI), `Index.dat` (binary index), `Data0000.dat`... (JPEG/PNG/BMP tile data and associated blobs). Associated blobs (thumbnail, barcode/label image, preview, scan map, stage-position map, `ScanDataLayer_XMLInfoHeader`, `ProfileXMLHeader`/`ProfileXML` = scan profile XML, `VIMSLIDE_HISTOGRAM_DATA`) are inside the .dat files, listed in `[HIERARCHICAL]` NONHIER entries. The content of the XML blobs is not documented publicly *(to confirm)*.
OpenSlide exposes **every** key of every INI group as `mirax.<GROUP>.<KEY>` (source: add_properties); three are normalised: `openslide.objective-power` (GENERAL.OBJECTIVE_MAGNIFICATION), `openslide.mpp-x/y` (level-0 MICROMETER_PER_PIXEL_X/Y), plus `openslide.background-color` (IMAGE_FILL_COLOR_BGR). Associated images: `label` (ScanDataLayer_SlideBarcode), `macro` (ScanDataLayer_SlideThumbnail), `thumbnail` (ScanDataLayer_SlidePreview).
Sources: https://openslide.org/formats/mirax/ ; https://github.com/openslide/openslide/blob/main/src/openslide-vendor-mirax.c ; a real v2.2 Slidedat.ini pasted in https://github.com/libvips/libvips/issues/2614 (Pannoramic DESK, software 2.0.5.93613; slide invented data in the issue not reproduced here).

### 2.2 Field table (keys seen in the real sample; values below are invented lookalikes)
OS prop is `mirax.<section>.<key>`.

| Section.Key | Meaning | Format / example | Seen with | OS prop | Class |
|---|---|---|---|---|---|
| GENERAL.SLIDE_ID | GUID that ties Index.dat and Data*.dat to this slide (not a lab ID) | 32 hex, `3CED04DF52594E52A428B6A2FF0EE99C`-style | all versions | `mirax.GENERAL.SLIDE_ID` | SLIDE (indelible unique file identity; generated by scanner). Newer slides store UTF-16LE in data-file headers |
| GENERAL.SLIDE_NAME | Name shown in viewer; scanner default is counter-like, but the operator or barcode-naming can set it | `2021.1` (sample); may be `H22-0001179` | all | `mirax.GENERAL.SLIDE_NAME` | **AMBIGUOUS (high risk)**: free text, frequently the accession/case no. |
| GENERAL.PROJECT_NAME | Scanner project/profile | `Pannoramic Slide Scanner` | all | `mirax.GENERAL.PROJECT_NAME` | AMBIGUOUS (may be study/project name; default is generic) |
| GENERAL.SLIDE_VERSION / CURRENT_SLIDE_VERSION | Slidedat format versions | `01.03` / `2.2` | all | `mirax.GENERAL.*` | SLIDE |
| GENERAL.SLIDE_CREATION_FINISHED | Scan completed flag | `True` | newer | `mirax.GENERAL.SLIDE_CREATION_FINISHED` | SLIDE |
| GENERAL.SLIDE_CREATIONDATETIME | Scan date/time, **local time, day-first locale string** | `17/06/2021 12:41:35` | all | `mirax.GENERAL.SLIDE_CREATIONDATETIME` | AMBIGUOUS (same as Philips; also locale-dependent parse risk: dd/mm vs mm/dd and no timezone). A `SLIDE_UTC_CREATIONDATETIME` key exists in other samples *(to confirm)* |
| GENERAL.SLIDE_TYPE | Modality | `SLIDE_TYPE_BRIGHTFIELD` (fluorescence variants *(to confirm)*) | all | same | SLIDE |
| GENERAL.SLIDE_CONTENT | | `DIGITAL_SLIDE` | | same | SLIDE |
| GENERAL.SLIDE_POSITION_X/Y | Slide position on stage (um) | `2500`, `22780` | | same | SLIDE |
| GENERAL.IMAGENUMBER_X/Y | Camera-FOV grid size | `936`, `2656` | | same | SLIDE (geometry) |
| GENERAL.IMAGE_OVERLAP_MICROMETERS_X/Y | Stitch overlap | `0` | | same | SLIDE |
| GENERAL.OBJECTIVE_MAGNIFICATION | Objective power (CaseViewer reports 2x different from OpenSlide/BF per HistoQC notes) | `40` | all | `mirax.GENERAL.OBJECTIVE_MAGNIFICATION`, `openslide.objective-power` | SLIDE |
| GENERAL.OBJECTIVE_NAME | Objective type | `Plan-Apochromat` | | same | SLIDE |
| GENERAL.CAMERA_TYPE | Camera model | `Point Grey GS3-U3-51S5M-C` | | same | SLIDE |
| GENERAL.ADAPTER_SIZE / OPTOVAR_SIZE | Camera adapter / optovar magnification | `1`, `1` | | same | SLIDE |
| GENERAL.CameraImageDivisionsPerSide | Tile subdivision | `8` | | same | SLIDE |
| GENERAL.VIMSLIDE_CAMERA_REAL_BITDEPTH / VIMSLIDE_SLIDE_BITDEPTH | Camera/storage bit depth | `24`, `8` | | same | SLIDE |
| GENERAL.CONFOCAL, DISK_POSITION | Confocal module state | `NO`, `0` | | same | SLIDE |
| GENERAL.FOCUS_MAP | Focus strategy | `AUTO` | | same | SLIDE (focus setting) |
| GENERAL.FOCUS_LIMIT, FOCUS_LIMIT_LO, FOCUS_LIMIT_UP | Z focus range (stage units) | `ENABLED`, `2190`, `2290` | | same | SLIDE (focus setting) |
| GENERAL.EXTENDED_FOCUS_ALGORITHM | EFI algorithm | `FL Image` | | same | SLIDE |
| GENERAL.FLAT_FIELD_CORRECTION | | `DISABLED` | | same | SLIDE |
| LAYER_0_LEVEL_n_SECTION.MICROMETER_PER_PIXEL_X/Y | um/px per pyramid level | `0.0867706237424547` | all | `mirax.LAYER_0_LEVEL_0_SECTION.MICROMETER_PER_PIXEL_X`, `openslide.mpp-x/y` | SLIDE |
| LAYER_0_LEVEL_n_SECTION.IMAGE_FORMAT / IMAGE_COMPRESSION_FACTOR | Tile codec and JPEG quality | `JPEG`, `80` | all | same | SLIDE (compression) |
| LAYER_0_LEVEL_n_SECTION.IMAGE_FILL_COLOR_BGR, DIGITIZER_WIDTH/HEIGHT, OVERLAP_X/Y, IMAGE_CONCAT_FACTOR | Geometry | `16777215`, `301`, `251`, ... | | same | SLIDE |
| LAYER_1_LEVEL_n_SECTION.* (fluorescence/filter): FILTER_NAME, EXCITATION_WAVELENGTH/BANDWIDTH, EMISSION_WAVELENGTH/BANDWIDTH, EXPOSUREPERCENTAGE, DIGITALGAIN, COLOR_R/G/B, ZSTACK_STEP_COUNT, ZSTACK_FIRST_LEVEL, EXTENDED_STEP_SIZE/COUNT, IS_MASTER_FILTER, IS_STITCHING_FILTER, ACTIVE, MODIFY, THRESHOLD, ZDIFF/XDIFF/YDIFF, VIMSLIDE_HISTOGRAM_DATA_CHANNEL_SIZE | Filter/channel and z-stack settings | `FITC`, `488` | all | same | SLIDE |
| LAYER_2_SECTION: EXTENDED_FOCUS_LEVEL, ZERO_FOCUS_LEVEL, LAST_Z_STACKED_ZOOM_LEVEL; LAYER_2_LEVEL_0_SECTION.OFFSET_IN_MICROMETERS | Focus-stack layout | `-1`, `0`, `9` | | same | SLIDE |
| NONHIERLAYER_0_SECTION.SCANNER_HARDWARE_VERSION | Scanner model | `Pannoramic DESK` | all | `mirax.NONHIERLAYER_0_SECTION.SCANNER_HARDWARE_VERSION` | SLIDE |
| NONHIERLAYER_0_SECTION.SCANNER_HARDWARE_ID | Scanner serial/ID | `PDESK-027910` | all | `...SCANNER_HARDWARE_ID` | SLIDE |
| NONHIERLAYER_0_SECTION.SCANNER_SOFTWARE_VERSION | Software build | `2.0.5.93613` | all | `...SCANNER_SOFTWARE_VERSION` | SLIDE |
| NONHIERLAYER_0_SECTION.SCANNER_CAMERA_TYPE | Camera | same as GENERAL | | same | SLIDE |
| NONHIERLAYER_0_SECTION.IccProfileColorScheme/WhitePoint/Gamma | ICC-related scalars (0 = none embedded in sample) | `0` | | same | SLIDE (ICC) |
| NONHIERLAYER_0_SECTION.SCANNING_TIME_IN_SEC, SCANNED_FOV_COUNT | Scan duration / FOV count | `1560`, `8221` | | same | SLIDE |
| NONHIERLAYER_0_SECTION.CAMERA_ROTATION, AVEGARE_IMAGE_OVERLAP_X/Y_IN_PIXELS (sic), OBJECT_GUIDE_HYSTERESIS_X/Y | Calibration/geometry | | | same | SLIDE |
| NONHIERLAYER_0_LEVEL_2_SECTION.THUMBNAIL_IMAGE_TYPE/WIDTH/HEIGHT; _LEVEL_3_ BARCODE_IMAGE_TYPE/WIDTH/HEIGHT/FLIP; _LEVEL_4_ PREVIEW_*; _LEVEL_0_ SCANMAP_*; _LEVEL_5_ STAGEPOSMAP_* | Associated-image descriptors | `JPEG`,`1701`,`1341` | | same | n/a; **label image = leak** |
| NONHIERLAYER_1_SECTION.DATA_FORMAT_VERSION; NONHIERLAYER_2_LEVEL_0_SECTION.COMPRESSED_STITCHING_*; NONHIERLAYER_3_SECTION.VIMSLIDE_HISTOGRAM_* | Stitching / histogram format | | | same | SLIDE (structure) |
| HIERARCHICAL.*, DATAFILE.* | Index structure, data file names | `Data0000.dat` | | same | n/a |

There is **no barcode text field** in the sample Slidedat.ini; the barcode exists as an image (`ScanDataLayer_SlideBarcode`, JPEG). Barcode text, if decoded, goes into SLIDE_NAME or the slide label/viewer database *(to confirm: Pannoramic Scanner software "slide name from barcode" setting)*. No stain field, no rack/slot beyond `DISK_POSITION` *(to confirm)*. Other versions/scanners (Pannoramic SCAN II, 250 Flash, MIDI) may add keys: `SLIDE_UTC_CREATIONDATETIME`, per-filter `LAYER_1` extras *(to confirm)*; the 3DHISTECH INI-handling doc page (3dhistech.com/data/pssm/website/Descriptions/INI_files.htm) returned 404.

---

## 3. Roche / Ventana (iScan Coreo, iScan HT, DP 200, DP 600): BIF and non-overlap TIFF

### 3.1 Where metadata lives
BigTIFF; **XMP tag 0x02BC** carries a UTF-8 XML `<Metadata>` blob in IFD 0 (overview), IFD 1 (probability image), IFD 2 (high-res scan). Also TIFF tags `ImageDescription`, `Software`, `DateTime`, `ICC Profile` (0x8773, IFD 2 only), private `IMAGE_DEPTH` (0x80E5) for focus layers.
Source: Roche Digital Pathology BIF whitepaper v1.0 (DP 200 only; iScan Coreo/HT explicitly not covered; DP 600 not mentioned) https://diagnostics.roche.com/content/dam/diagnostics/Blueprint/en/pdf/rmd/Roche-Digital-Pathology-BIF-Whitepaper.pdf ; OpenSlide https://openslide.org/formats/ventana/ ; https://github.com/openslide/openslide/blob/main/src/openslide-vendor-ventana.c ; Bio-Formats VentanaReader.java.
OpenSlide: **every attribute of the `iScan` element becomes `ventana.<AttributeName>`** (if non-empty); `openslide.mpp-x/y` from ScanRes, `openslide.objective-power` from Magnification; `tiff.Software`, `tiff.DateTime`, `tiff.ImageDescription` standard TIFF properties; `openslide.icc-size`. Only iScan attributes are exposed; SlideInfo/EncodeInfo/PreScanData are parsed but not exposed. Bio-Formats: `ImageDescription` tokens (level, mag, quality) become series metadata; XML parsed internally (ScanRes, tile joints).
Associated images: `macro` (IFD "Label Image"/"Label_Image", the whole slide overview incl. label), `thumbnail`.

### 3.2 Field table (DP 200 whitepaper; types per Roche)

| XML path / tag | Attribute | Meaning, format, invented example | Written by | OS prop | Class |
|---|---|---|---|---|---|
| IFD0 `/Metadata/iScan` | `ScannerModel` | const `VENTANA DP 200` (whitepaper: stop if not equal) | DP 200; DP 600 `VENTANA DP 600` *(to confirm)* | `ventana.ScannerModel` | SLIDE |
| | `UnitNumber` | scanner serial, uint >= 2000000, e.g. `2012345` | DP | `ventana.UnitNumber` | SLIDE |
| | `BuildVersion` | scanning software version `1.0.0.1551` | DP | `ventana.BuildVersion` | SLIDE |
| | `BuildDate` | `m/d/yyyy H:M:S PM`, e.g. `1/17/2018 0:7:11 PM` | DP | `ventana.BuildDate` | SLIDE |
| | `Mode` | const `Brightfield` | DP | `ventana.Mode` | SLIDE |
| | `Magnification` | `20` or `40` | DP, Coreo/HT | `ventana.Magnification`, `openslide.objective-power` | SLIDE |
| | `ScanRes` | um/px: `0.465` (20x) / `0.25` (40x) | all | `ventana.ScanRes`, `openslide.mpp-x/y` | SLIDE |
| | `Z-layers` | odd number of focal planes, e.g. `3` | DP | `ventana.Z-layers` | SLIDE (focus setting) |
| | `Z-spacing` | plane separation um, `1.0` | DP | `ventana.Z-spacing` | SLIDE |
| | `UserName` | Windows username of operator, e.g. `Operator` | DP | `ventana.UserName` | AMBIGUOUS (personnel identifier; may be a named person) |
| | `Barcode1D`, `Barcode2D` | decoded barcode text, if detected | DP | `ventana.Barcode1D`, `ventana.Barcode2D` | **AMBIGUOUS (high risk)**: lab-defined; accession/case/slide id; Roche slides carry Ventana's own label stock with stain/protocol codes *(to confirm)* |
| | `ScanWhitePoint` | white pixel value (uint8) for empty tiles | DP | `ventana.ScanWhitePoint` | SLIDE |
| | `SlideAnnotation` | NA per Roche; free text? | DP | `ventana.SlideAnnotation` | AMBIGUOUS (free text; unspecified) |
| | `ShowLabel`, `LabelBoundary`, `FocusMode`, `FocusQuality`, `ScanMode` | listed "NA"; FocusMode/FocusQuality/ScanMode are focus/scan settings | DP | `ventana.*` | SLIDE (focus: `FocusMode`, `FocusQuality`, `ScanMode`) |
| | `Anonymization` | boolean: label anonymised? | DP | `ventana.Anonymization` | SLIDE (but flags whether label removal was applied) |
| `iScan/AOI0..N-1` | `Left, Top, Right, Bottom` | AOI rectangle in slide physical coords | DP | not exposed | SLIDE |
| `iScan/ProcessingParameters/Registration`, `/Color` | NA | | | | |
| IFD1 `/Metadata/PreScanData` | `SlideIdentifier` | "Internal slide name" (also in `AOIParameters`) | DP | not exposed | **AMBIGUOUS (high risk)**: internal name; often barcode/accession-derived *(to confirm)* |
| | `SizeImage`, `PixelsPerUnit`, `Unit`, `PixelMode` | probability image geometry | | | SLIDE |
| IFD1 `.../AOIn` | `Index, Identifier, Valid, SizeImage, Rectangle, ...` ; `AnchorPointSet` (`SizeAOI, FrameStep, FrameCountAOI, FocusTime`), `AnchorPoint` (`Point, FrameCoord, Density`) | AOI/focus anchor grid | | | SLIDE |
| IFD1 `/Metadata/AOIParameters` | `SlideIdentifier, XEnd, YStart, CornerGrayValue, FolderPath, AOIApproach, AOIRectExtendDim, MergeDistance, Probability, BackupFocus, ...` | AOI detection params; **`FolderPath` = scanner file path (NA)**, may embed operator/case folder names | | | AMBIGUOUS (`FolderPath`, `SlideIdentifier`) |
| IFD2 `/Metadata/EncodeInfo` | `Ver` (>=2) | | DP | not exposed | SLIDE |
| `EncodeInfo/SlideInfo` | `Rack`, `Slot` | **rack and slot in scanner** (NA to decoding) | DP | not exposed | SLIDE (user wants rack/slot) |
| | `BaseName` | internal file name, "ignore" | DP | not exposed | **AMBIGUOUS (leak)**: original base filename |
| `SlideInfo/SlideStitchInfo`, `ImageInfo`, `TileJointInfo`, `AoiOrigin` | Left/Top/Right/Bottom; AOIScanned, AOIIndex, NumRows, NumCols, Width, Height, Pos-X, Pos-Y; FlagJoined, Confidence, Direction, Tile1, Tile2, OverlapX, OverlapY | tiling/stitch | DP, Coreo/HT (older versions) | used for geometry, not exposed | SLIDE (structure) |
| TIFF `ImageDescription` (IFD2) | tokens `level=0 mag=40 quality=95` | pyramid level, magnification, **JPEG quality 70-100** | DP | `tiff.ImageDescription` | SLIDE (compression quality) |
| TIFF `ImageDescription` IFD0 | `Label_Image` (Coreo: `Label Image`) | | | | |
| TIFF `Software` | `ScanOutputManager 1.0.0.15101` | writer name/version | DP | `tiff.Software` | SLIDE |
| TIFF `DateTime` | `2018:08:22 16:54:15` (local, no zone) | scan date and time | DP | `tiff.DateTime` | AMBIGUOUS (as above) |
| TIFF `ICC_PROFILE` (0x8773, IFD2, ICC v4) | scanner colour profile | | DP | `openslide.icc-size` | SLIDE |
| TIFF `IMAGE_DEPTH` 0x80E5 | focus layer count | | DP | - | SLIDE |

iScan Coreo/HT: same BIF container with different (older) iScan attributes; OpenSlide exposes whatever is present, so exact names are only known from real files *(to confirm)*. Whitepaper says the DP 200 also writes ordinary non-overlapping `.tiff` BigTIFF whose metadata "differ to some extent" *(to confirm exact differences)*. DP 600: no public document found *(to confirm)*; Roche's public statement is the DP 200 whitepaper.

---

## 4. Zeiss Axioscan 7 / Axioscan.Z1 (CZI)

### 4.1 Where metadata lives
ZISRAW container: `ZISRAWFILE` header, `ZISRAWMETADATA` segment with a single XML document `<ImageDocument><Metadata>...`, `ZISRAWSUBBLOCK`s (each with its own small XML, ignored by OpenSlide), `ZISRAWATTDIR` + `ZISRAWATTACH` attachments: `Label` (nested CZI), `SlidePreview` (nested CZI), `Thumbnail` (JPG). Compression: JPEG XR common; also uncompressed 24/48 bpp, zstd0/zstd1; JPEG/LZW in spec (unsupported by OpenSlide).
The ZISRAW design specification is **confidential** (Zeiss licence request page); field names below come from Bio-Formats and OpenSlide source.
Sources: https://openslide.org/formats/zeiss/ ; https://github.com/openslide/openslide/blob/main/src/openslide-vendor-zeiss.c ; https://github.com/ome/bioformats/blob/develop/components/formats-gpl/src/loci/formats/in/ZeissCZIReader.java ; https://www.zeiss.com/microscopy/en/products/software/zeiss-zen/czi-format-license-request.html
OpenSlide: walks `/ImageDocument/Metadata/{AttachmentInfos,DisplaySetting,Information,Scaling}` generically, property = `zeiss.<dotted path>` (list items keyed by `Id` or `Name` attribute); `openslide.barcode` = first `AttachmentInfos/AttachmentInfo/Label/Barcodes/Barcode/Content`; mpp = 1e6 * `zeiss.Scaling.Items.X.Value` (metres); objective power via `zeiss.Information.Image.ObjectiveSettings.ObjectiveRef.Id` -> `zeiss.Information.Instrument.Objectives.<id>.NominalMagnification`. Bio-Formats: pipe-joined path keys, e.g. `Information|Image|AcquisitionDateAndTime`.

### 4.2 Field table (names that Bio-Formats/OpenSlide read; Axioscan-specific extras *(to confirm)*)

| XML path (under ImageDocument/Metadata) | Meaning / example | OS prop | BF key | Class |
|---|---|---|---|---|
| Information/Application/Name, Version | `ZEN`, `3.9.1` (software) *(element names to confirm)* | `zeiss.Information.Application.Name` / `.Version` *(to confirm)* | `Information|Application|Name` | SLIDE |
| Information/Document/Name, Title, Description, Comment, Author, UserName, CreationDate | Free text by operator or auto-name; `CreationDate` `2025-03-02T14:03:11.1234567+01:00` ISO with tz | `zeiss.Information.Document.*` | `Information|Document|*` | Name/Title/Description/Comment: **AMBIGUOUS (free text, high risk)**; CreationDate: AMBIGUOUS (date); UserName: AMBIGUOUS (personnel) |
| Information/User/DisplayName, FirstName, LastName, MiddleName, Email, Institution, UserName | ZEN operator profile | `zeiss.Information.User.*` | `Information|User|*` | AMBIGUOUS (personnel; PII of staff, not patient) |
| Information/Image/AcquisitionDateAndTime | scan time with tz | `zeiss.Information.Image.AcquisitionDateAndTime` | `Information|Image|AcquisitionDateAndTime` | AMBIGUOUS |
| Information/Image/SizeX, SizeY, SizeS (scenes), SizeC, SizeZ, SizeM, ComponentBitCount, PixelType | geometry | `zeiss.Information.Image.Size*` | same | SLIDE |
| Information/Image/ObjectiveSettings/ObjectiveRef/Id, Medium, RefractiveIndex, CorrectionCollar | Selected objective | `zeiss.Information.Image.ObjectiveSettings.*` | | SLIDE |
| Information/Image/Dimensions/Channels/Channel/* (ExposureTime, IlluminationType, DetectorSettings/Binning, ColorMode, PixelType, Fluor...) | camera and channel settings | `zeiss.Information.Image.Dimensions.Channels.*` | | SLIDE (exposure, focus-adjacent settings) |
| Information/Instrument/Microscopes/Microscope/{Id,Name,Type,System}/Manufacturer/{Manufacturer,Model,SerialNumber,LotNumber} | Scanner identity: e.g. `Axioscan 7`, serial `7412345678` *(element specifics to confirm; Bio-Formats reads `Manufacturer`, `Model`, `SerialNumber`)* | `zeiss.Information.Instrument.Microscopes.<id>...` | `Information|Instrument|Microscopes|Microscope|Manufacturer|*` | SLIDE |
| Information/Instrument/Objectives/Objective/{Manufacturer/Model, NominalMagnification, LensNA, WorkingDistance, Immersion, PupilGeometry, Correction} | Objective | `zeiss.Information.Instrument.Objectives.<id>.NominalMagnification` (+others) | `Information|Instrument|Objectives|Objective|*` | SLIDE |
| Information/Instrument/Detectors/Detector/{Manufacturer/Model, SerialNumber, Type, Gain, GammaDefault ...} | Camera; note GammaDefault needed for Axioscan 7 colour (OpenSlide docs: 0.45 for Axiocam705c/AxioCamEL, 1 for Axiocam712m) | `zeiss.Information.Instrument.Detectors.<id>.GammaDefault` | | SLIDE |
| Information/Instrument/{LightSources, Filters, FilterSets, Dichroics, ...} | illumination/optics | | | SLIDE |
| Information/Environment/Temperature, AirPressure, Humidity, CO2Percent | | | | SLIDE (scan-time condition) |
| Scaling/Items/Distance[@Id=X|Y]/Value | metres per pixel `2.2E-07` | `zeiss.Scaling.Items.X.Value`, `openslide.mpp-x` | `Scaling|Items|Distance|Value` | SLIDE |
| DisplaySetting/Channels/Channel/* (Gamma, ColorMode, ...) | display only | `zeiss.DisplaySetting.*` | | SLIDE (display) |
| AttachmentInfos/AttachmentInfo/Label/Barcodes/Barcode/Content (and Type/Position) | Barcode text(s) from the label; Zeiss clinical config can use barcode to name files | `zeiss.AttachmentInfos...Content`, `openslide.barcode` | `AttachmentInfos|...|Barcode|Content` *(key form to confirm)* | **AMBIGUOUS (high risk)** |
| Experiment/ExperimentBlocks/AcquisitionBlock/... (TilesSetup, scan profile, focus strategy, autofocus) | scan profile and focus settings | not walked by OpenSlide (only the 4 subtrees) | `Experiment|...` | SLIDE (focus settings), *(Axioscan element names to confirm)* |
| Attachments `Label`, `SlidePreview`, `Thumbnail` | images | `label`, `macro`, `thumbnail` | | leak |
| CZI file name | default from barcode when configured | n/a | | **leak** |

---

## 5. Olympus / Evident (VS110/VS120/VS200: VSI + ETS)

### 5.1 Where metadata lives
`<name>.vsi` is a TIFF-like container with proprietary typed tag tree (tag IDs are numbers; Bio-Formats maps ID to a name); pixel data in `_<name>_/stack1/frame_t.ets` (ETS: JPEG/JPEG2000/raw/etc.). OpenSlide does not read VSI. Bio-Formats CellSensReader does: names in `getTagName`, stored via `addGlobalMeta`/series meta as `<tagPrefix><tagName>`; datetime tags converted from Unix seconds.
Source: https://github.com/ome/bioformats/blob/develop/components/formats-gpl/src/loci/formats/in/CellSensReader.java (tag IDs in constants).

### 5.2 Field table (BF key = tag name as shown, tag ID in brackets)

| BF tag name [ID] | Meaning, invented example | Class |
|---|---|---|
| Slide Bar Code [120635] | decoded barcode text | **AMBIGUOUS (high risk)** |
| Tray No. [120638], Slide No. [120637] | **loader tray and slide position (rack/slot analogue)** | SLIDE |
| Slide Name [2061], Slide Info [2060] | name/notes, free text | **AMBIGUOUS (high risk)** |
| Specimen [2055], Tissue [2057], Preparation [2058], Staining [2059] | free-text slide properties entered at scan (stain, tissue); only vendor with stain tag | AMBIGUOUS: stain/tissue/preparation are SLIDE-type but free text (may contain identifiers) |
| Document Name [11], Document Note [13], Document Author [15], Document Company [16] | file title, note, author, company | AMBIGUOUS (free text; author is personnel) |
| Document Creation Time [14], Creation time (UTC) [2015] | Unix seconds | AMBIGUOUS (date) |
| Document creator name/major/minor/sub version [17-20], Product Build Number [21], creator package [22], Document product / product name / version [23-25], Product Name [34], Product Version [35] | software identity `cellSens Dimension`, `VS-ASW 3.2` | SLIDE |
| Device Name [120116], Device Type [120117], Device Unit ID [120129], Device Subtype [120130], Device Model [120132], Device Manufacturer [120133] | per-device (microscope, camera, objective changer, slide loader) names, model, **unit ID (serial-like)** | SLIDE |
| Magnification [120060 Objective mag], Numerical Aperture [120061], Objective Working Distance [120062], Objective Name [120063], Objective Type [120064], Objective Refractive Index [120079], Objective Description/Subtype/Lens, TV Adapter Magnification [120050] | objective | SLIDE |
| Original magnification [1073741824], Physical pixel size [20007 plane scale], Origin [20006] | um/px | SLIDE |
| Exposure time (microseconds), Camera gain/offset/gamma/sharpness/channel gains, Binning, Camera bit depth [BIT_DEPTH], ICC enabled [100030], Contrast/Brightness, Autoexposure ..., Camera white balance/colorspace/..., Camera HDRI ... | acquisition settings | SLIDE |
| Z start / increment / value, Z stack settings, EFI (Extended focal imaging) stack/maps, Focus image | focus settings | SLIDE |
| Scanning Time (seconds) [175209], Snapshot Count [175208] | | SLIDE |
| Image Type, Tile system [20004], External file present [20005], External file volume [20025], Default image, Overview image, Macro image, Sample mask | structure; overview/macro are leak risks | n/a / leak |
| Compression: ETS header compression code (RAW, JPEG, JPEG2000, JPEG lossless, PNG, BMP per CellSens constants) and quality | | SLIDE |
No OpenSlide property names (not supported). VS200 may add keys *(to confirm)*; Evident documents (VS200 white papers) not retrieved.

---

## 6. Grundium (Ocus 20/40, Ocus M series)

* Export formats per Grundium/vendor pages: SVS, TIFF, SZI, DICOM (DICOM availability stated inconsistently; Grundium FAQ framed as 2025). Legacy manual MGU-00001 v6.0 (could not be retrieved in full) says export to USB/web; annotations are not exported.
* FAQ (https://www.grundium.com/faq/): label is part of the overview image saved "as part of the metadata"; barcode info can be used to name the image file; no integrated barcode reader (separate reader), the M series lists QR/Data Matrix support.
* opentile-go lists Grundium among non-vendor TIFF authoring handled by its generic TIFF reader and as a DICOM sample source. No ImageDescription specification found.
* **Field table: not obtainable from primary sources.** *(to confirm)* by inspecting an Ocus SVS/TIFF with `tiffinfo`/`openslide-show-properties`. If SVS is written Aperio-style, OpenSlide would expose `aperio.*` (ImageDescription `|`-separated keys such as `AppMag`, `MPP`, `Date`, `Time`, `ScanScope ID`, `Filename`). That is an inference, not confirmed.
* Class guidance: filename (barcode-derived) and overview image are leak sources.

## 7. Motic (EasyScan One/Pro/Pro6, FlexScan60)

* Pathomation (https://realdata.pathomation.com/?p=680) lists Motic MDS as a multi-file format; Slide Score supports it (https://slidescore.nki.nl/news/a/015_motic). A Motic brochure says FlexScan60 can export QPTIFF/SVS. A published DICOM conversion study used an EasyScan Pro6.
* No public format specification, no OpenSlide or Bio-Formats reader found. **No field list.** *(to confirm)* by contacting Motic (SDK) or inspecting `.mds`/`.mdsx` sets.

## 8. KFBio (KFB / KFBF)

Source: kfb2zarr Rust parser (third party; reverse-engineered) https://docs.rs/crate/kfb2zarr/0.1.3/source/src/parser.rs and `types.rs`; OpenSlide users list May 2024 states no support. Python `kfbslide` wrapper exposes only `openslide.vendor`, `openslide.mpp-x/y`, `openslide.objective-power` and associated images `macro`/`label`/`thumbnail`.

| Header field (little-endian offset) | Meaning | Example | Class |
|---|---|---|---|
| magic `F1 01 EE EE` @0x00; bytes 4..8 `KFBF` => fluorescence | format | | SLIDE |
| `tile_count` i32 @0x10 | tiles | | SLIDE |
| `base_height` i32 @0x14, `base_width` i32 @0x18 | size (swapped in KFBF) | | SLIDE |
| `scan_scale` i32 @0x1C | scan magnification | `20`/`40` | SLIDE |
| `spend_time` i32 @0x28 | scan duration s | `540` | SLIDE |
| `scan_time` i32 @0x2C | **Unix time of scan** | `1745000000` | AMBIGUOUS (date) |
| `image_cap_res` f32 @0x4C | um/px | `0.2500` | SLIDE |
| `kfb_tile_size` i32 @0x58 | tile size | `256` | SLIDE |
| KFBF channel TLV @0xA8-0x200: tags 0x4D names (40-byte UTF-8), 0x4F colours (3 x u32), 0x54 exposures (f64 ms); `channel_count` BE u32 @0xB0 | fluorescence channels/exposure | `DAPI`, `45.0` | SLIDE |
| Tile info: magnification f32 per tile | | | SLIDE |
| Label and thumbnail sections (width/height/spp/len + JPEG) | associated images | | leak |
No barcode text, scanner model, serial, software version, or stain appears in the parsed header. *(Other KFB header bytes unparsed; the Chinese KFB SDK header dictionary was not enumerated on its public page.)* Compression: JPEG tiles.

## 9. Sakura SVSlide (.svslide; Sakura Finetek/Tissue-Tek Scan)

SQLite 3 database written with the eXpress Persistent Objects ORM. Source: https://openslide.org/formats/sakura/ ; https://github.com/openslide/openslide/blob/main/src/openslide-vendor-sakura.c . No public sample files.

| Table.column | Meaning | OS prop | Class |
|---|---|---|---|
| SVSlideDataXPO.SlideId | Slide identifier (lab-assigned or barcode) | `sakura.SlideId` | **AMBIGUOUS (high risk)** |
| SVSlideDataXPO.Date | Scan date | `sakura.Date` | AMBIGUOUS (date) |
| SVSlideDataXPO.Description | free text | `sakura.Description` | **AMBIGUOUS (free text, high risk)** |
| SVSlideDataXPO.Creator | user/creator | `sakura.Creator` | AMBIGUOUS (personnel) |
| SVSlideDataXPO.Keywords | free text | `sakura.Keywords` | **AMBIGUOUS (high risk)** |
| SVSlideDataXPO.DiagnosisCode | **diagnosis code field** | `sakura.DiagnosisCode` | PATIENT-adjacent (clinical data about the specimen/patient): exclude from I2S slide set |
| SVSlideDataXPO.HRScanCount, TotalDataSizeBytes, m_labelScan, m_overviewScan | counts, size, label/macro images | not exposed except images | label/macro = leak |
| SVHRScanDataXPO.ScanId, Name, Date, Description | scan id/name/date/text | `sakura.ScanId` (Name, Description not exposed) | AMBIGUOUS |
| SVHRScanDataXPO.ResolutionMmPerPix | mm/px | `sakura.ResolutionMmPerPix`, `openslide.mpp-x/y` (*1000) | SLIDE |
| SVHRScanDataXPO.NominalLensMagnification | objective | `sakura.NominalLensMagnification`, `openslide.objective-power` | SLIDE |
| SVHRScanDataXPO.FocussingMethod (sic), FocusStack, PosOnSlideMm | focus | `sakura.FocussingMethod` | SLIDE (focus setting) |
| SVScannedImageDataXPO.* | label/macro images, positions | images | leak |
| unique table `++VersionBytes`, `Header` blob (tile size, dims, focal planes) | format version, geometry | `sakura.VersionBytes` | SLIDE |
No scanner model/serial/software version recorded in the tables OpenSlide reads *(to confirm: other tables may exist)*.

---

## 10. Fields that commonly leak identity unintentionally

| Vendor | Leak vector | Why |
|---|---|---|
| Philips | `PIM_DP_UFS_BARCODE` (Base64) | accession/case/part/block/level; Base64 is not protection |
| Philips | label image and macro image (`LABELIMAGE`/`MACROIMAGE`, `PIM_DP_IMAGE_DATA`; TIFF "Label"/"Macro" IFDs) | printed text, barcode, handwriting |
| Philips | `DICOM_DERIVATION_DESCRIPTION` in TIFF export contains `sourceFilename=` (per OpenSlide parser: "stops at sourceFilename") | original file name; **verify on real file** *(to confirm exact content)* |
| Philips | file name of .isyntax/.tiff | often barcode or accession *(to confirm)* |
| Philips | `PIIM_DP_SCANNER_OPERATOR_ID` | staff identity |
| Philips | Separate DICOM WSI export | DICOM patient/study modules (patient name, ID, accession) |
| 3DHistech | `GENERAL.SLIDE_NAME`, `PROJECT_NAME` | free text; barcode-as-name |
| 3DHistech | `ScanDataLayer_SlideBarcode` (label image), `ScanDataLayer_SlideThumbnail` (macro) | label |
| 3DHistech | name of the .mrxs and folder; `ScanDataLayer_XMLInfoHeader`/`ProfileXML` blobs | filename; undocumented XML *(to confirm contents)* |
| Roche | `Barcode1D`, `Barcode2D`, `SlideIdentifier`, `BaseName`, `FolderPath`, `UserName`, `SlideAnnotation` | text / paths / user |
| Roche | IFD0 overview image (whole slide incl. label), `Anonymization` flag | image; flag says whether it was removed |
| Zeiss | `Barcode/Content`, `Document/Name/Title/Description/Comment`, `User/*`, `Label` and `SlidePreview` attachments, file name derived from barcode | text / images |
| Olympus | `Slide Bar Code`, `Slide Name`, `Slide Info`, `Document Name/Note/Author/Company`, Specimen/Tissue/Preparation/Staining free text, overview/macro/label images | text / images |
| Grundium | label inside overview image; barcode used to name the file | per Grundium FAQ |
| Sakura | `SlideId`, `Description`, `Keywords`, `DiagnosisCode`, label/macro images | text / images |
| KFB | label/thumbnail images, file name | images |
| All | TIFF `Artist`, `HostComputer`, `Copyright`, `DocumentName` tags (OpenSlide exposes as `tiff.Artist`, `tiff.HostComputer`, `tiff.Copyright`, `tiff.DocumentName`) | operator/computer names |
| All | OpenSlide DICOM backend: "many DICOM attributes" exposed as `dicom.*` with no stated filtering | may include `dicom.PatientName`/`PatientID` *(to confirm)* |

## 11. Proposed I2S SLIDE vocabulary derived from the above (minimum cross-vendor set)

Reliable across at least one scanner family (source in brackets):
* scanner.manufacturer, scanner.model, scanner.serial (Philips `DICOM_DEVICE_SERIAL_NUMBER`; 3DHistech `SCANNER_HARDWARE_ID`; Roche `UnitNumber`; Zeiss Microscope Manufacturer/SerialNumber; Olympus `Device Unit ID`)
* scanner.software_version(s), scanner.firmware (Philips `DICOM_SOFTWARE_VERSIONS`; 3DHistech `SCANNER_SOFTWARE_VERSION`; Roche `BuildVersion`/`BuildDate`/TIFF `Software`; Zeiss Application Version; Olympus Product Version)
* scanner.last_calibration date/time + status (Philips only)
* scan.mode / modality (Roche `Mode`, 3DHistech `SLIDE_TYPE`)
* optics.objective_power, objective name, NA (all but Philips/KFB where only implicit/scale)
* image.mpp_x/mpp_y (all)
* focus: focus mode, z-layers, z-spacing, focus limits (Roche `Z-layers`/`Z-spacing`/`FocusMode`; 3DHistech `FOCUS_MAP`/`FOCUS_LIMIT*`; Olympus Z stack tags; Sakura `FocussingMethod`)
* compression: codec, quality/ratio, lossy flag (Philips method/ratio; Roche `quality`; 3DHistech `IMAGE_FORMAT`/`IMAGE_COMPRESSION_FACTOR`; Zeiss codec per subblock)
* ICC profile (Philips `DICOM_ICCPROFILE`; Roche ICC tag; 3DHistech Icc* scalars)
* scan.rack / slot / tray (Philips rack/slot/priority; Roche `Rack`/`Slot`; Olympus `Tray No.`/`Slide No.`; 3DHistech `DISK_POSITION` *(to confirm meaning)*)
* scan duration, FOV count (3DHistech, Olympus, KFB)
* stain/specimen (only Olympus has tags; free text) - not recoverable from other vendors' files.

AMBIGUOUS (put behind policy, not in the indelible block by default): all barcodes; slide name/id/title/description/keywords/comment; scan date/time (offer date-only or hashed time); operator/user/author names; file names; overview/label/macro images.

## 12. Source list (all read 2026-11-24)
* OpenSlide format pages: https://openslide.org/formats/{philips,ventana,mirax,zeiss,sakura,dicom}/ ; https://openslide.org/docs/properties/
* OpenSlide source (main): https://github.com/openslide/openslide/tree/main/src : `openslide-vendor-philips-tiff.c`, `-ventana.c`, `-mirax.c`, `-sakura.c`, `-zeiss.c`, `-dicom.c`, `openslide-decode-tifflike.c`
* Bio-Formats: https://github.com/ome/bioformats : `VentanaReader.java`, `ZeissCZIReader.java`, `CellSensReader.java` (develop branch)
* tifffile: https://github.com/cgohlke/tifffile (`philips_metadata`, `series_philips`, `series_ventana`)
* libisyntax: https://github.com/amspath/libisyntax (`src/isyntax/isyntax.c`)
* isyntax2raw (Glencoe): https://github.com/glencoesoftware/isyntax2raw
* TileBio iSyntax deid hackathon repo (secondary, PolyForm Noncommercial; field names only used): https://github.com/TileBio/ISyntaxDEID-Hackathon-Edition
* libvips issue with real Slidedat.ini: https://github.com/libvips/libvips/issues/2614
* Roche BIF whitepaper v1.0: https://diagnostics.roche.com/content/dam/diagnostics/Blueprint/en/pdf/rmd/Roche-Digital-Pathology-BIF-Whitepaper.pdf
* kfb2zarr (docs.rs) 0.1.3 `parser.rs`, `types.rs`; kfbslide PyPI
* Grundium FAQ https://www.grundium.com/faq/ ; Pathomation https://realdata.pathomation.com/?p=680 ; Slide Score https://slidescore.nki.nl/news/a/015_motic
* Zeiss CZI format licence page https://www.zeiss.com/microscopy/en/products/software/zeiss-zen/czi-format-license-request.html
* Not read (failed): OpenSlide users mailing-list archive (TLS certificate error; not bypassed), 3dhistech.com INI_files.htm (404), Grundium manual PDF (connection refused).
