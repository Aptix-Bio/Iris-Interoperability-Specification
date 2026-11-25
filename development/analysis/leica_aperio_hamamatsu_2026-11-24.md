# Scan-time metadata: Leica/Aperio (SVS, SCN) and Hamamatsu (NDPI, VMS/VMU)
Date read for all sources: 2026-11-24. Invented example values only. "(tc)" = to confirm (not verified in a primary source I could open).

## Sources
- S1 https://openslide.org/formats/aperio/ ; S2 /formats/leica/ ; S3 /formats/hamamatsu/
- S4 openslide src/openslide-vendor-aperio.c, -leica.c, -hamamatsu.c (raw.githubusercontent.com/openslide/openslide/main/src/)
- S5 tifffile.py (raw.githubusercontent.com/cgohlke/tifffile/master/tifffile/tifffile.py): NDPI_TAGS registry, svs_description_metadata, is_svs/is_scn, tags 55000-55004
- S6 Hamamatsu NDPI SDK tag list https://nanozoomer.hamamatsu.com/us/en/SDK-API/Our-file-format.html
- S7 Bio-Formats readers (github.com/ome/bioformats develop, components/formats-gpl/src/loci/formats/in/SVSReader.java, NDPIReader.java, LeicaSCNReader.java)
- S8 Bio-Formats SVS metadata support page https://www-legacy.openmicroscopy.org/site/support/bio-formats5.1/_sources/formats/aperio-svs-tiff-metadata.txt
- S9 real SVS ImageDescription (CMU-1, Aperio Image Library v10.0.51) quoted in openslide-users, https://marc.info/?l=openslide-users&m=142526652409694&w=2
- S10 OpenSlide man page (3.4.1) https://manpages.debian.org/buster/libopenslide-dev/openslide-formats.3
- Not obtained: Aperio's "Digital Slides and Third-party Data Interchange" PDF (the authoritative key list; not fetched), Leica SCN XSD, NCI deid PDF (login wall), ImageScope manual (binary, unreadable via fetch). A web search result (image.sc/openslide-users, unfetched snippet) reports key values `Parmset = USM Filter`, `ICC Profile = AT2`, `ScanScope ID = LCA-AT1-SHY`, `Aperio Image Library v12.0.16`, a "Scan to (this computer)" Parmset: (tc, snippet only).

---
## 1. Aperio SVS (AT2, GT450, ScanScope CS/XT/CS2, Versa-as-SVS)

### Where metadata lives (S1, S4, S5, S9)
- Single TIFF/BigTIFF, tiled JPEG (7) or JPEG 2000 (33003 YCbCr / 33005 RGB). Detection: first IFD tiled and ImageDescription starts "Aperio".
- ImageDescription (tag 270) of IFD 0 (full resolution; also repeated in lower pyramid levels with downsample info instead of full keys, "at least the full-resolution image").
- Syntax: `<Header>|<k> = <v>|<k> = <v>...`. Split on `|`; first token is a free header (S4 ignores it). Each token split on first `=`, key and value whitespace-stripped. Header form (S9): `Aperio Image Library v10.0.51\r\n46920x33014 [0,100 46000x32914] (256x256) JPEG/RGB Q=30|AppMag = 20|...` — header line 2 carries pixel size, ROI box, tile size, codec and JPEG quality (not key=value; parse by pattern).
- Example (S9 structure, invented values): `Aperio Image Library v12.0.16\n46920x33014 [0,100 46000x32914] (256x256) JPEG/RGB Q=70|AppMag = 20|StripeWidth = 2048|ScanScope ID = XX1234|Filename = CASE-0001|Date = 01/31/26|Time = 09:59:15|User = 00000000-0000-0000-0000-000000000000|Parmset = USM Filter|MPP = 0.4990|Left = 25.69|Top = 23.45|LineCameraSkew = -0.0004|LineAreaXOffset = 0.0192|LineAreaYOffset = -0.0003|Focus Offset = 0.000000|ImageID = 1000000|OriginalWidth = 46920|Originalheight = 33014|Filtered = 5|ICC Profile = ScanScope v1`
- IFD layout: IFD0 baseline; IFD1 thumbnail (stripped, always); further tiled IFDs = pyramid; trailing stripped IFDs: NewSubfileType 1 = label, 9 = macro (S1,S4). Label/macro ImageDescription also begins "Aperio" and contains "label WxH" / "macro WxH" (S7: segments containing "label"/"macro").
- ICC profile: standard TIFF tag 34675 of IFD0; name also in `ICC Profile` key (S1, S4, S9: 141992 bytes).
- Private tags: tifffile registry lists 55000 AperioUnknown55000, 55001 AperioMagnification, 55002 AperioMPP, 55003 AperioScanScopeID, 55004 AperioDate (S5). Likely very old ScanScope files; not written by current scanners (tc).
- OpenSlide: every key becomes `aperio.<key>` (spaces kept, e.g. `aperio.ICC Profile`, `aperio.Focus Offset`). OpenSlide reads no other fields. Standard TIFF tags also exposed as `tiff.*` (Make, Model, Software, DateTime if present) (tc for what scanners fill).

### Fields (key, spelling exact)
Keys confirmed in a real file: S9. Keys confirmed by Bio-Formats parser: S7. Others (tc).

| Key | Meaning | Format / example | Writers | OpenSlide property | Class |
|---|---|---|---|---|---|
| (header) `Aperio Image Library vX.Y.Z` | Software/library version that wrote file | `Aperio Image Library v12.0.16` | all (S9; v10.0.51 ScanScope CS; v12.0.16 seen on AT-class, snippet tc). GT450 header text `Aperio Leica Biosystems GT450 v1.0.1` (tc) | not exposed separately (tiff.ImageDescription holds all; first token in `openslide.comment`) | SLIDE |
| line 2 `WxH [x,y wxh] (tw x th) CODEC/COLOR Q=n` | full pixel size, scanned ROI, tile size, codec, JPEG quality | `46920x33014 [0,100 46000x32914] (256x256) JPEG/RGB Q=70` | all (S9) | none | SLIDE |
| `AppMag` | objective magnification | number `20`, `40` | all (S9, S7) | `aperio.AppMag`; `openslide.objective-power` | SLIDE |
| `MPP` | microns per pixel (square) | `0.4990` | all (S9, S7) | `aperio.MPP`; `openslide.mpp-x`, `openslide.mpp-y` | SLIDE |
| `StripeWidth` | scan stripe width in pixels | `2040` | all (S9) | `aperio.StripeWidth` | SLIDE |
| `ScanScope ID` | scanner unit identifier (serial-like) | `CPAPERIOCS`, `SS1234` | all (S9) | `aperio.ScanScope ID` | SLIDE (device serial; not a person) |
| `Filename` | name of slide file/ID at scan, typically the label barcode or accession-derived string | `CMU-1` | all (S9) | `aperio.Filename` | AMBIGUOUS (leak risk, see below) |
| `Date` | scan date | `MM/DD/YY` e.g. `01/31/26` | all (S9; S7 parses with Time as `MM/dd/yy HH:mm:ss`) | `aperio.Date` | AMBIGUOUS (scan date is slide-scan characteristic but a date linked to a case may identify under HIPAA date rules) |
| `Time` | scan time | `HH:MM:SS` | all | `aperio.Time` | AMBIGUOUS (same) |
| `Time Zone` | UTC offset of scan time | `GMT-05:00` | newer scanners (tc) | `aperio.Time Zone` | SLIDE (tc) |
| `User` | operator/scan user id | GUID `00000000-...` (S9) | all (S9) | `aperio.User` | AMBIGUOUS (pseudonymous GUID, may map to staff; could be PATIENT-adjacent? no, person but staff) |
| `Parmset` | scan parameter set name | `USM Filter` | all (S9) | `aperio.Parmset` | SLIDE |
| `Left`, `Top` | physical position of scanned area from slide edge, mm | `25.691574` | all (S9, S7 as PositionX/Y) | `aperio.Left`, `aperio.Top` | SLIDE |
| `LineCameraSkew`, `LineAreaXOffset`, `LineAreaYOffset` | line-scan camera calibration | float | ScanScope line-scan (S9) | `aperio.*` same names | SLIDE |
| `Focus Offset` | focus offset applied | `0.000000` | all (S9) | `aperio.Focus Offset` | SLIDE |
| `ImageID` | internal image ID (DB id at scan) | integer `1004486` | all (S9) | `aperio.ImageID` | AMBIGUOUS (internal DB key linking back to LIS/eSlide record) |
| `OriginalWidth`, `Originalheight` (sic, lowercase h) | dimensions before cropping | int | all (S9) | `aperio.OriginalWidth`, `aperio.Originalheight` | SLIDE |
| `Filtered` | filtering count/flag | int `5` | all (S9) | `aperio.Filtered` | SLIDE |
| `ICC Profile` | embedded ICC profile name | `ScanScope v1`, `AT2` (tc snippet) | all (S9) | `aperio.ICC Profile`; profile bytes via TIFF 34675 | SLIDE |
| `Title` | free text slide title | text | ImageScope/eSlide-edited, some scanners (tc) | `aperio.Title` | PATIENT-risk (free text) |
| `Exposure Time`, `Exposure Scale` | camera exposure (value x scale = seconds) | `8`, `0.000001` | newer (S7 parses) | `aperio.Exposure Time`, `aperio.Exposure Scale` | SLIDE |
| `DisplayColor` | display colour (fluorescence/AFI) | int | AFI/fluorescence (S7) | `aperio.DisplayColor` | SLIDE |
| `Emission Wavelength`, `Excitation Wavelength` | fluorescence channel wavelengths | nm | ScanScope FL/AFI (S7) | `aperio.*` | SLIDE |
| `Dye` | stain/fluor dye name per channel | `DAPI` | FL (S7) | `aperio.Dye` | SLIDE (stain) |
| `OffsetZ`, `TotalDepth` | Z-stack offset / depth | float | Z-stack (S7) | `aperio.OffsetZ`, `aperio.TotalDepth` | SLIDE |
| `SessonMode` (sic), `DSR ID`, `Exposure Time` etc. | newer scanner session/DSR fields | (tc) | AT2/GT450 (tc, memory only) | `aperio.*` | (tc) |
| `Make`/`Model`/`Software` TIFF tags | scanner make/model/software | `Aperio` / `AT2` (tc) | (tc) | `tiff.Make`... | SLIDE (tc) |
| Stain name, accession, case, specimen, UDI, firmware, rack/slot | NOT keys of the SVS spec I could verify. Barcode content lives only in the label image (and in LIS), `Filename` is often derived from it. | | | | |

Count: 16 header/line-2 + key=value fields confirmed in S9, plus 9 more parsed in S7 (Emission/Excitation Wavelength, Dye, Left/Top already counted, TotalDepth, OffsetZ, Exposure Time/Scale, DisplayColor, Title (tc)) = about 27 distinct fields; ~20 confirmed in a real file or code, remainder (tc).
Also: compression (TIFF 259: 7, 33003, 33005), JPEG quality in line 2, ICC.

---
## 2. Leica SCN (SCN400, Aperio Versa)

### Where metadata lives (S2, S4, S7)
- BigTIFF; ImageDescription of IFD0 holds one XML document (ends `</scn>`; tifffile detects by `</scn>` suffix, S5). Namespaces `http://www.leica-microsystems.com/scn/2010/03/10` or `/2010/10/01`.
- Hierarchy (from S4/S7): `scn > collection[name, uuid, sizeX, sizeY, barcode(2010/03/10 attr), ocr] > barcode (2010/10/01 child element text, Base64) ; image[name, uuid] > creationDate, device[model, version], pixels > dimension[r,z,c,sizeX,sizeY,ifd], view[sizeX,sizeY,offsetX,offsetY,spacingZ], scanSettings > illuminationSettings > illuminationSource, numericalAperture ; scanSettings > objectiveSettings > objective ; supplementalImage[type, ifd]`. Sizes/offsets in nm. Macro image = image at (0,0) with size = collection.
- Example (invented): `<scn xmlns="http://www.leica-microsystems.com/scn/2010/10/01"><collection name="..." uuid="..." sizeX="..." sizeY="..."><barcode>QUJDMTIz</barcode><image name="..." uuid="..."><creationDate>2026-01-31T09:59:15.000Z</creationDate><device model="Leica SCN400" version="1.0"/><pixels>...</pixels><view .../><scanSettings><objectiveSettings><objective>20</objective></objectiveSettings><illuminationSettings><numericalAperture>0.4</numericalAperture><illuminationSource>brightfield</illuminationSource></illuminationSettings></scanSettings></image></collection></scn>` (element layout from S4 XPaths; value formats (tc)).
- TIFF XResolution/YResolution (unit cm) give MPP.

| XML field | Meaning | Example | OpenSlide property | Class |
|---|---|---|---|---|
| `collection/@barcode` or `collection/barcode` | slide barcode text (Base64 in 2010/10/01; OpenSlide >=3.4.1 decodes) | `ABC123` | `leica.barcode`, `openslide.barcode` | AMBIGUOUS (accession/case barcode, leak risk) |
| `collection/@ocr` | OCR of label text | (tc) | none (S7 original metadata only) | PATIENT-risk (OCR of label can include name) |
| `collection/@name`, `image/@name` | collection/image names | text | none | AMBIGUOUS (may embed case ID) |
| `collection/@uuid`, `image/@uuid` | unique ids | GUID | none | SLIDE |
| `creationDate` | scan time | ISO 8601 (tc) | `leica.creation-date` | AMBIGUOUS (scan date) |
| `device/@model` | scanner model | `Leica SCN400` | `leica.device-model` | SLIDE |
| `device/@version` | scanner software/firmware version | `1.0.0` | `leica.device-version` | SLIDE |
| `illuminationSource` | `brightfield` or fluorescence | `brightfield` | `leica.illumination-source` | SLIDE |
| `objective` | objective power | `20` | `leica.objective`, `openslide.objective-power` | SLIDE |
| `numericalAperture` | objective NA | `0.4` | `leica.aperture` | SLIDE |
| `view/@sizeX,sizeY,offsetX,offsetY,spacingZ` | physical extent, position, Z spacing (nm) | int | `openslide.region[n].*`, `openslide.bounds-*` (derived) | SLIDE |
| `dimension/@r,z,c,sizeX,sizeY,ifd` | pyramid/focal/channel layout | int | none | SLIDE |
| `supplementalImage/@type` | extra image kind (macro etc.) | | associated image `macro` | SLIDE |
| `ResolutionUnit`/`XResolution` | MPP | | `openslide.mpp-x/y` | SLIDE |

14 fields. Compression (JPEG/BigTIFF tags), ICC (tc: not mentioned in S2/S4/S7).
Not found: serial number, stain, rack/slot, UDI (tc).

---
## 3. Hamamatsu NDPI (NanoZoomer S60, S210, S360, XR, 2.0-HT)

### Where metadata lives (S3, S4, S5, S6)
- TIFF-like with 64-bit IFD offsets, little-endian; strings always out-of-line (S6). libtiff cannot read it. Standard tags: 256, 257, 271 Make, 272 Model, 282/283/296 resolution, 305 Software, 306 DateTime (S6). IFDs: pyramid levels (65421 Magnification > 0), macro (65421 = -1), tissue map/mask (65421 = -2), optional focal-plane IFDs (65424).
- Private tags 65324-65500 (S5 registry vs S6 SDK page). 65449 "Comments/Calibration Info" is CRLF-separated `key=value` (S4: split "\r\n", then first "="): keys seen in Bio-Formats: `Product` (model), `NDP.S/N` (serial), `Objective.Lens.Magnificant` (sic) (S7). Other keys (tc).
- OpenSlide exposes names: `hamamatsu.SourceLens`, `hamamatsu.XOffsetFromSlideCentre`, `hamamatsu.YOffsetFromSlideCentre`, `hamamatsu.Reference`, and every 65449 pair as `hamamatsu.<key>`. All other tags ignored (S4). MPP via TIFF resolution (`openslide.mpp-x/y`), plus `tiff.*`.

| Tag | Name (S6 / S5) | Type | Meaning | Example | OpenSlide | Class |
|---|---|---|---|---|---|---|
| 271 / 272 / 305 | Make / Model / Software | ASCII | scanner make, model, software | `Hamamatsu` / `C13210-01` / `NDP.scan 3.2` (invented) | `tiff.Make`, `tiff.Model`, `tiff.Software` | SLIDE |
| 306 | DateTime | ASCII | write date/time | `2026:01:31 09:59:15` | `tiff.DateTime` | AMBIGUOUS (scan date) |
| 282/283/296 | resolutions | | pixel pitch | | `openslide.mpp-x/y` | SLIDE |
| 65420 | Version / FileFormat | LONG | NDPI version (1) | 1 | none | SLIDE |
| 65421 | Lens/Image Type / Magnification | FLOAT | objective-equivalent magnification; -1 macro, -2 map | 20.0 | `hamamatsu.SourceLens`, `openslide.objective-power` | SLIDE |
| 65422/65423/65424 | Physical X/Y/Z | SLONG | offset from slide centre, nm; Z focus | | `hamamatsu.XOffsetFromSlideCentre`, `...Y...`; Z none | SLIDE |
| 65425 | TissueIndex | (tc) | tissue section index | | none | SLIDE (tc) |
| 65426 / 65432 | MCU starts / high | LONG[] | JPEG restart offsets | | none | SLIDE (structural) |
| 65427 | Reference / SlideLabel | ASCII | slide reference string (user/label text) | `CASE-0001-A1` | `hamamatsu.Reference` | AMBIGUOUS (free text, commonly accession or name) |
| 65428 | AuthCode | (tc) | | | none | (tc) |
| 65434 | FilterSetName / Fluorescence | ASCII | FL filter set | | none | SLIDE |
| 65435-65438 | ExposureRatio, Red/Green/BlueMultiplier | SLONG | exposure and channel gains | | none | SLIDE |
| 65439 / 65440 | FocusPoints / Regions | SLONG[] | focus map (x,y,z) | | none | SLIDE |
| 65441 | CaptureMode | SLONG | imaging mode | | none | SLIDE |
| 65442 | Hardware serial / ScannerSerialNumber | ASCII | scanner serial | `1234567` | none (but `hamamatsu.NDP.S/N` from 65449) | SLIDE |
| 65444 | JpegQuality | SLONG | compression quality | 80 | none | SLIDE |
| 65445 / 65446 | RefocusInterval / FocusOffset | SLONG | autofocus params | | none | SLIDE |
| 65447 | BlankLines | (tc, S5 only) | | | none | SLIDE |
| 65448 | FirmwareVersion | ASCII | | | none | SLIDE |
| 65449 | Comments / Calibration Info (property map) | ASCII | `Product=`, `NDP.S/N=`, `Objective.Lens.Magnificant=`, other keys (tc) | `Product=NanoZoomer S360` | `hamamatsu.<key>` | SLIDE |
| 65450 | LabelObscured | LONG | label masked flag | 0/1 | none | SLIDE (relevant to PHI) |
| 65451 | Wavelength | FLOAT | emission nm | | none | SLIDE |
| 65453 | LampAge | LONG | hours | | none | SLIDE |
| 65454 | ExposureTime | LONG | microseconds (S7) | | none | SLIDE |
| 65455 / 65456 / 65457 | FocusTime / ScanTime / WriteTime | LONG | seconds | | none | SLIDE |
| 65458 | FullyAutoFocus | LONG | flag | | none | SLIDE |
| 65468-65475 | Barcode...Barcode8 | ASCII | up to 8 barcode decodes (S5 names Barcode, Barcode2...) | `ABC123` | none | AMBIGUOUS |
| 65476 | MedicalRegulation | ASCII | `RUO`, `IVR`, `USA` | | none | SLIDE |
| 65477 | ScanProfile | XML (S5) | scan profile XML | (tc content) | none | SLIDE (tc) |
| 65480 | BarcodeType | (S5 only) | barcode symbology | | none | SLIDE (tc) |
| 65500 | DefaultGamma | S5/S7 | | | none | SLIDE |

About 36 distinct tags/fields. Not present: stain, UDI, rack/slot, objective NA (tc).

---
## 4. Hamamatsu VMS / VMU (legacy NanoZoomer; multi-file, INI)
- `.vms`/`.vmu` INI file, group `[Virtual Microscope Specimen]` (VMS, JPEG) or `[Uncompressed Virtual Microscope Specimen]` (VMU, NGR). Sidecars: JPEG tile files, `MapFile`, `OptimisationFile`, `.ngr`. Every key exposed `hamamatsu.<key>` (S3, S4); `SourceLens` -> `openslide.objective-power`; `PhysicalWidth/Height` (nm per image) -> mpp via `openslide.mpp-x/y`.
- VMS keys: NoLayers, NoJpegColumns, NoJpegRows, ImageFile (ImageFile(x,y), ImageFile(z,x,y)), MapFile, OptimisationFile, AuthCode, SourceLens, PhysicalWidth, PhysicalHeight, LayerSpacing, MacroImage, PhysicalMacroWidth, PhysicalMacroHeight, XOffsetFromSlideCentre, YOffsetFromSlideCentre.
- VMU adds: MapScale, PixelWidth, PixelHeight, LayerOffset, Reference, BitsPerPixel (must be 36), PixelOrder (RGB), Creator, IlluminationMode, ExposureMultiplier, GainRed/Green/Blue, FocalPlaneTolerance, NMP, MacroIllumination, FocusOffset, RefocusInterval, CubeName, HardwareModel, HardwareSerial, NoFocusPoints, FocusPointNX/Y/Z, NoBlobPoints, BlobPointNBlob, BlobPointNFocusPoint, BlobMapWidth, BlobMapHeight (S3).
- Class: SLIDE for optical/geometry/focus/hardware (SourceLens, Physical*, Offsets, Gain*, Exposure*, Illumination*, CubeName, HardwareModel, HardwareSerial, Creator (software)); AMBIGUOUS: `Reference` (free text), `ImageFile*`/`MapFile` names (filenames, case in name); `AuthCode` (internal, (tc)).
- ~19 VMS and ~62 VMU keys.

---
## 5. Identity-leak candidates (all formats)
1. Filename on disk (SVS names usually accession-derived), plus SVS `Filename` key (S9), NDPI `Reference`, VMS/VMU `ImageFile`/`Reference`/`MapFile` names.
2. Label image (SVS IFD subfile type 1; NDPI SlideLabel/macro images; SCN macro with label region) often prints name, MRN, DOB, barcodes. OpenSlide label/macro associated images.
3. Barcode content: SCN `barcode` / `ocr`, NDPI tags 65468-65475, SVS in label only.
4. Free text: SVS `Title`/`Comment` (tc), NDPI 65449 other keys (tc), 65427.
5. Macro image (shows label if on the slide).
6. Dates/times: SVS `Date`/`Time`, `creationDate`, TIFF DateTime (indirect identifier).
7. `User` GUID and `ImageID` (back-references to staff/DB).
8. Aperio ImageScope-added annotations/Title edits written back into the file (tc).

## 6. Unconfirmed
- Full Aperio key list for AT2/GT450 (Time Zone, Title, DSR ID, SessonMode, GT450 header string): Aperio interchange PDF not read.
- SCN XML sample and exact value formats; serial/stain/UDI/rack/slot presence in SCN.
- NDPI 65449 full key set, 65428 AuthCode, 65425, 65447, 65477/65480 contents; S60/S210/S360/2.0-HT differences by model.
- VMS/VMU written by which model (NanoZoomer 2.0-HT/RS legacy).
- No ICC or UDI field found in SCN/NDPI primary sources.
