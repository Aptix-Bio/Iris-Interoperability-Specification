# DICOM VL Whole Slide Microscopy Image IOD: acquisition, specimen and optics attributes

Research for the I2S attribute vocabulary (.iris slide files). Read only; no repository was edited.

## Sources and method

- Standard: DICOM PS3.3 2026e (the "Current" edition as of 2026-11-25), chunked HTML at https://dicom.nema.org/medical/dicom/current/output/chtml/part03/ and the PS3.6 data dictionary at https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_6.html.
- The section pages were downloaded raw and their tables extracted directly (scripts in `i2s_research/totable.py`, `i2s_research/gen.py`). The WebFetch summaries were not used for attribute data: the first pass summarized the C.8.12.4 table without VR/keywords and mislabeled sections, so it was discarded.
- VR and VM and keywords come from PS3.6 chapter 6. Requirement types (1/1C/2/2C/3) come from the PS3.3 module tables. Module tables in PS3.3 do not list VR, so VR and VM are PS3.6 values.
- "Seq/Coded": SQ means a sequence. "Coded" means a Code Sequence macro (PS3.3 Table 8.8-1, Code Value / Coding Scheme / Code Meaning items). Coded attributes are flattened by I2S only if we accept the code-meaning text.

## Section number corrections

Several section numbers in the brief were wrong. Verified mapping:

| Brief said | Actual | Notes |
|---|---|---|
| C.8.12.13 Optical Path Module | C.8.12.5 Optical Path Module | C.8.12.13 is the **Dermoscopic Image Module** (its Table C.8.12.13-1 holds Recognizable Visual Features, Light Source Polarization, Contact Method, Immersion Media, Optical Magnification Factor, Tracking ID/UID, none of which are in the WSM IOD). Verified from the Next link on sect_C.8.12.14.html. Its attribute table was read from a WebFetch summary, not raw HTML, so treat those rows as unverified. |
| C.8.12.9 WSM Series | C.8.12.3 Whole Slide Microscopy Series Module | C.8.12.9 is the WSM Frame Type macro (Whole Slide Microscopy Image Frame Type Sequence 0040,0710). |
| C.7.6.16 Enhanced General Equipment | C.7.5.2 Enhanced General Equipment | C.7.6.16 is Multi-frame Functional Groups; Pixel Measures macro is C.7.6.16.2.1. |
| C.8.12.4.1.3 for total matrix | C.8.12.14 Microscope Slide Layer Tile Organization | C.8.12.4.1.3 only cross-references C.8.12.14.1.1. |
| Focus Method / EDoF / Z (separate module) | Inside C.8.12.4 (WSM Image Module) | Attributes (0048,0011)-(0048,0014) are in the WSM Image Module table. |
| Specimen C.7.6.22 | C.7.6.22 Specimen Module (correct) | Stain/prep is in C.7.6.22.1.3 (Specimen Preparation Sequence, BTID 8001). |
| Multi-frame Functional Groups: Pixel Measures / Plane Position / Optical Path ID | Pixel Measures C.7.6.16.2.1; Plane Position (Slide) C.8.12.6.1; Optical Path Identification C.8.12.6.2 | Shared/per-frame usage in A.32.8.4. |

The IOD module table is at https://dicom.nema.org/medical/dicom/current/output/chtml/part03/sect_A.32.8.3.html (Table A.32.8-1). The IOD description is at sect_A.32.8.1.html. The E-R model is sect_A.32.8.2.html.

## IOD module table (PS3.3 Table A.32.8-1)

Usage as printed in sect_A.32.8.3.html. "M" mandatory, "C" conditional, "U" user optional.

| IE | Module | Section | Usage |
|---|---|---|---|
| Patient | Patient | C.7.1.1 | M |
| Patient | Clinical Trial Subject | C.7.1.3 | U |
| Study | General Study | C.7.2.1 | M |
| Study | Patient Study | C.7.2.2 | U |
| Study | Clinical Trial Study | C.7.2.3 | U |
| Series | General Series | C.7.3.1 | M |
| Series | Whole Slide Microscopy Series | C.8.12.3 | M |
| Series | Clinical Trial Series | C.7.3.2 | U |
| Frame of Reference | Frame of Reference | C.7.4.1 | C (required if Image Type value 3 is VOLUME or THUMBNAIL) |
| Equipment | General Equipment | C.7.5.1 | M |
| Equipment | Enhanced General Equipment | C.7.5.2 | M |
| Acquisition | General Acquisition | C.7.10.1 | M |
| Multi-Resolution Pyramid | Multi-Resolution Pyramid | C.7.11.1 | U (only if Image Type value 3 is VOLUME or THUMBNAIL) |
| Image | General Image | C.7.6.1 | M |
| Image | General Reference | C.12.4 | U |
| Image | Microscope Slide Layer Tile Organization | C.8.12.14 | M |
| Image | Image Pixel | C.7.6.3 | M |
| Image | Acquisition Context | C.7.6.14 | M |
| Image | Multi-frame Functional Groups | C.7.6.16 | M |
| Image | Multi-frame Dimension | C.7.6.17 | M |
| Image | Specimen | C.7.6.22 | M |
| Image | Whole Slide Microscopy Image | C.8.12.4 | M |
| Image | Optical Path | C.8.12.5 | M |
| Image | Slide Label | C.8.12.8 | C (required if Image Type value 3 is LABEL; may be present otherwise) |
| SOP Common | SOP Common | C.12.1 | M |
| SOP Common | Common Instance Reference | C.12.2 | M |
| SOP Common | Frame Extraction | C.12.3 | C |

Note: the Patient, General Study, General Series, General Equipment, Enhanced General Equipment and General Acquisition modules are all M in this IOD. The Patient module (name, ID, birth date, sex) is therefore mandatory content in every WSM instance, which matters for PHI (see the last section).

The SOP Class UID 1.2.840.10008.5.1.4.1.1.77.1.6 is not printed on the A.32.8 pages fetched. It should be checked in PS3.4 Annex B (not fetched in this pass). Unverified here.

## Functional group macros (A.32.8.4, sect_A.32.8.4.html)

| Macro | Section | Usage |
|---|---|---|
| Pixel Measures | C.7.6.16.2.1 | M (shared) |
| Frame Content | C.7.6.16.2.2 | U (must not be shared) |
| Referenced Image | C.7.6.16.2.5 | U |
| Derivation Image | C.7.6.16.2.6 | C |
| Real World Value Mapping | C.7.6.16.2.11 | U (MONOCHROME2 only) |
| Plane Position (Slide) | C.8.12.6.1 | C (required if Dimension Organization Type is not TILED_FULL) |
| Optical Path Identification | C.8.12.6.2 | C (same condition) |
| Specimen Reference | C.8.12.6.3 | U |
| WSM Image Frame Type | C.8.12.9 | M (shared) |

## Attribute tables

Each row: keyword, tag, VR, VM from PS3.6; module section; requirement type from the PS3.3 table; description cut to 150 characters from the standard's text. Full text is at the section URLs under https://dicom.nema.org/medical/dicom/current/output/chtml/part03/ (for example sect_C.8.12.4.html, sect_C.8.12.5.html, sect_C.8.12.14.html, sect_C.7.6.22.html, sect_C.7.5.2.html, sect_C.7.5.html, sect_C.7.6.html, sect_C.7.10.html, sect_C.7.2.html, sect_C.7.3.html, sect_C.7.html for the Patient module).


### Optics

| Keyword | Tag | VR | VM | Module | Type | Seq/Coded | Meaning (from table) |
|---|---|---|---|---|---|---|---|
| OpticalPathSequence | (0048,0105) | SQ | 1 | Optical Path (C.8.12.5) | 1 | SQ | Describes the optical paths used during the acquisition of this image. One or more Items shall be included in this Sequence. See Section C.8.12.5.1.1 |
| OpticalPathIdentifier (nested) | (0048,0106) | SH | 1 | Optical Path ID (C.8.12.6.2) | 1 |  | Identifier referencing an Item of Optical Path Sequence (0048,0105) |
| OpticalPathDescription (nested) | (0048,0107) | ST | 1 | Optical Path (C.8.12.5) | 3 |  | Description of the optical path specified in the Sequence Item. |
| IlluminatorTypeCodeSequence (nested) | (0048,0100) | SQ | 1 | Optical Path (C.8.12.5) | 3 | SQ | Type of illuminator. Only a single Item is permitted in this Sequence. |
| IlluminationWaveLength (nested) | (0022,0055) | FL | 1 | Optical Path (C.8.12.5) | 1C |  | Nominal wavelength of the illuminator in nm. Required if Illumination Color Code Sequence (0048,0108) is not present. May be present otherwise. |
| IlluminationColorCodeSequence (nested) | (0048,0108) | SQ | 1 | Optical Path (C.8.12.5) | 1C | SQ | Color of the illuminator. Only a single Item shall be included in this Sequence. Required if Illumination Wave Length (0022,0055) is not present. May ... |
| IlluminationTypeCodeSequence (nested) | (0022,0016) | SQ | 1 | Optical Path (C.8.12.5) | 1 | SQ | Coded value for illumination method. See Section C.8.12.5.1.2. One or more Items shall be included in this Sequence. |
| LightPathFilterTypeStackCodeSequence (nested) | (0022,0017) | SQ | 1 | Optical Path (C.8.12.5) | 3 | SQ | Filters used in the light source (excitation) path. One or more Items are permitted in this Sequence. See Section C.8.12.5.1.3. |
| LightPathFilterPassThroughWavelength (nested) | (0022,0001) | US | 1 | Optical Path (C.8.12.5) | 3 |  | Nominal pass-through wavelength of light path filter(s) in nm. |
| LightPathFilterPassBand (nested) | (0022,0002) | US | 2 | Optical Path (C.8.12.5) | 3 |  | Pass band of light path filter(s) in nm. This Attribute has two Values. The first Value is the shorter and the second Value the longer wavelength rela... |
| ImagePathFilterTypeStackCodeSequence (nested) | (0022,0018) | SQ | 1 | Optical Path (C.8.12.5) | 3 | SQ | Describes stack of filters used in image (emission) path between the imaging target and the optical sensor. One or more Items are permitted in this Se... |
| ImagePathFilterPassThroughWavelength (nested) | (0022,0003) | US | 1 | Optical Path (C.8.12.5) | 3 |  | Nominal pass-through wavelength of image path filter(s) in nm. |
| ImagePathFilterPassBand (nested) | (0022,0004) | US | 2 | Optical Path (C.8.12.5) | 3 |  | Pass band of image path filter(s) in nm. This Attribute has two Values. The first Value is the shorter and the second Value the longer wavelength rela... |
| LensesCodeSequence (nested) | (0022,0019) | SQ | 1 | Optical Path (C.8.12.5) | 3 | SQ | Lenses that were used in this optical path. One or more Items are permitted in this Sequence. |
| CondenserLensPower (nested) | (0048,0111) | DS | 1 | Optical Path (C.8.12.5) | 3 |  | Nominal power of the condenser lens. |
| ObjectiveLensPower (nested) | (0048,0112) | DS | 1 | Optical Path (C.8.12.5) | 3 |  | Nominal power of the objective lens. If a single lens is used as both condenser and objective, its power is specified in this Attribute. |
| ObjectiveLensNumericalAperture (nested) | (0048,0113) | DS | 1 | Optical Path (C.8.12.5) | 3 |  | Nominal numerical aperture of the objective lens. |
| ChannelDescriptionCodeSequence (nested) | (0022,001A) | SQ | 1 | Optical Path (C.8.12.5) | 1C | SQ | Describes the light color sensed for each channel to generate the image. Required if this differs from the natural interpretation. Note For MONOCHROME... |
| PaletteColorLookupTableSequence (nested) | (0048,0120) | SQ | 1 | Optical Path (C.8.12.5) | 3 | SQ | For MONOCHROME2 images, provides a transform of the pixel values with this optical path into an RGB color representation. The LUT provides a mapping t... |
| ICCProfile (nested) | (0028,2000) | OB | 1 | Optical Path (C.8.12.5) | 1C |  | An ICC Profile encoding the transformation of device-dependent stored pixel values into PCS-Values. See Section C.8.12.5.1.4 Required if Photometric I... |
| ColorSpace (nested) | (0028,2002) | CS | 1 | Optical Path (C.8.12.5) | 3 |  | A label that identifies the well-known color space of the image. Shall be consistent with any ICC Profile (0028,2000) that is also present. See Sectio... |
| NumberOfOpticalPaths | (0048,0302) | UL | 1 | Optical Path (C.8.12.5) | 1C |  | Number of Items in the Optical Path Sequence (0048,0105). Required if Dimension Organization Type (0020,9311) is present with a Value of TILED_FULL. M... |
| PixelSpacing (nested) | (0028,0030) | DS | 2 | Pixel Measures macro (C.7.6.16.2.1) | 1C |  | Physical distance between pixel centers in mm, row spacing then column spacing |
| SliceThickness (nested) | (0018,0050) | DS | 1 | Pixel Measures macro (C.7.6.16.2.1) | 1C |  | Nominal slice thickness or depth of field for optical imaging, in mm |
| TotalPixelMatrixColumns | (0048,0006) | UL | 1 | Tile Organization (C.8.12.14) | 1 |  | Total number of columns in pixel matrix; i.e., width of total imaged volume in pixels. See Section C.8.12.14.1.1 |
| TotalPixelMatrixRows | (0048,0007) | UL | 1 | Tile Organization (C.8.12.14) | 1 |  | Total number of rows in pixel matrix; i.e., height of total imaged volume in pixels. See Section C.8.12.14.1.1 |
| TotalPixelMatrixOriginSequence | (0048,0008) | SQ | 1 | Tile Organization (C.8.12.14) | 1 | SQ | Location of pixel 1\1 of the total pixel matrix in the Slide Coordinate System Frame of Reference. Only a single Item shall be included in this Sequen... |
| ImageOrientationSlide | (0048,0102) | DS | 6 | Tile Organization (C.8.12.14) | 1C |  | The direction cosines of the first row and the first column of the total pixel matrix with respect to the Slide Coordinate System Frame of Reference. ... |
| TilesOverlap | (0048,0304) | CS | 1 | Tile Organization (C.8.12.14) | 3 |  | Whether or not tiles in this Instance overlap with one or more adjacent tiles in the same Instance. Enumerated Values: ALL All tiles overlap with at l... |
| ImagedVolumeWidth | (0048,0001) | FL | 1 | WSM Image (C.8.12.4) | 1C |  | Width of total imaged volume (distance in the direction of rows in each Frame) in mm. See Section C.8.12.4.1.2 Required if Image Type (0008,0008) Valu... |
| ImagedVolumeHeight | (0048,0002) | FL | 1 | WSM Image (C.8.12.4) | 1C |  | Height of total imaged volume (distance in the direction of columns in each Frame) in mm. See Section C.8.12.4.1.2 Required if Image Type (0008,0008) ... |
| ImagedVolumeDepth | (0048,0003) | FL | 1 | WSM Image (C.8.12.4) | 1C |  | Depth of total imaged volume (distance in the Z direction of focal planes) in µm. See Section C.8.12.4.1.2 Required if Image Type (0008,0008) Value 3 ... |

### Focus-Z

| Keyword | Tag | VR | VM | Module | Type | Seq/Coded | Meaning (from table) |
|---|---|---|---|---|---|---|---|
| FocusMethod | (0048,0011) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Method of focusing image Enumerated Values: AUTO autofocus MANUAL includes any human adjustment or verification of autofocus |
| ExtendedDepthOfField | (0048,0012) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Image pixels were created through combining of image acquisition at multiple focal planes (focus stacking). Enumerated Values: YES NO |
| NumberOfFocalPlanes | (0048,0013) | US | 1 | WSM Image (C.8.12.4) | 1C |  | Number of acquisition focal planes used for extended depth of field. Required if Extended Depth of Field (0048,0012) Value is YES Note Total Pixel Mat... |
| DistanceBetweenFocalPlanes | (0048,0014) | FL | 1 | WSM Image (C.8.12.4) | 1C |  | Distance between acquisition focal planes used for extended depth of field, in µm. Required if Extended Depth of Field (0048,0012) Value is YES. Note ... |
| TotalPixelMatrixFocalPlanes | (0048,0303) | UL | 1 | Tile Organization (C.8.12.14) | 1C |  | Total number of focal planes (Z locations) in the pixel matrix; i.e., depth of total imaged volume in pixels. See Section C.8.12.14.1.1 Required if Di... |
| SpacingBetweenSlices (nested) | (0018,0088) | DS | 1 | Pixel Measures macro (C.7.6.16.2.1) | 1C |  | Center-to-center spacing between slices in mm; required for TILED_FULL |
| ZOffsetInSlideCoordinateSystem (nested) | (0040,074A) | DS | 1 | Plane Position (Slide) (C.8.12.6.1) | 1 |  | Z offset in um from the glass substrate reference plane; required even for a single focal plane |
| DimensionOrganizationType | (0020,9311) | CS | 1 | Multi-frame Dimension (C.7.6.17) | 3 |  | Dimension organization of the Instance. Defined Terms: 3D Spatial Multi-frame Image of equally spaced parallel planes (3D volume set) 3D_TEMPORAL Temp... |
| DimensionOrganizationSequence | (0020,9221) | SQ | 1 | Multi-frame Dimension (C.7.6.17) | 1 | SQ | Sequence that lists the Dimension Organization UIDs referenced by the containing SOP Instance. See Section C.7.6.17.2 for further explanation. One or ... |
| DimensionIndexSequence | (0020,9222) | SQ | 1 | Multi-frame Dimension (C.7.6.17) | 1C | SQ | Identifies the Sequence containing the indices used to specify the dimension of the multi-frame object. One or more Items shall be included in this Se... |
| ImageCenterPointCoordinatesSequence | (0040,071A) | SQ | 1 | Slide Coordinates (C.8.12.2) | 2 | SQ | The coordinates of the center point of the Image in the Slide Coordinate System Frame of Reference. Zero or one Item shall be included in this Sequenc... |
| OpticalPathIdentificationSequence | (0048,0207) | SQ | 1 | Optical Path ID (C.8.12.6.2) | 1 | SQ | Identifies the optical path characteristics of this Frame. Only a single Item shall be included in this Sequence. |

### Specimen-Stain

| Keyword | Tag | VR | VM | Module | Type | Seq/Coded | Meaning (from table) |
|---|---|---|---|---|---|---|---|
| ContainerIdentifier | (0040,0512) | LO | 1 | Specimen (C.7.6.22) | 1 |  | The identifier for the container that contains the specimen(s) being imaged. See Section C.7.6.22.1.1. |
| IssuerOfTheContainerIdentifierSequence | (0040,0513) | SQ | 1 | Specimen (C.7.6.22) | 2 | SQ | Organization that assigned the Container Identifier. Zero or one Item shall be included in this Sequence. |
| AlternateContainerIdentifierSequence | (0040,0515) | SQ | 1 | Specimen (C.7.6.22) | 3 | SQ | Sequence of alternate identifiers for the container that contains the specimen(s) being imaged. These may have been assigned, e.g., by the manufacture... |
| ContainerTypeCodeSequence | (0040,0518) | SQ | 1 | Specimen (C.7.6.22) | 2 | SQ | Type of container that contains the specimen(s) being imaged. Zero or one Item shall be included in this Sequence. |
| ContainerDescription | (0040,051A) | LO | 1 | Specimen (C.7.6.22) | 3 |  | Description of the container. |
| ContainerComponentSequence | (0040,0520) | SQ | 1 | Specimen (C.7.6.22) | 3 | SQ | Description of one or more components of the container (e.g., description of the slide and of the coverslip). One or more Items are permitted in this ... |
| SpecimenDescriptionSequence | (0040,0560) | SQ | 1 | Specimen (C.7.6.22) | 1 | SQ | Sequence of identifiers and detailed description of the specimen(s) being imaged. One or more Items shall be included in this Sequence. Each specimen ... |
| SpecimenIdentifier (nested) | (0040,0551) | LO | 1 | Specimen (C.7.6.22) | 1 |  | A departmental information system identifier for the Specimen. See Section C.7.6.22.1.1 and Section C.7.6.22.1.2. If a single specimen is present in a... |
| SpecimenUID (nested) | (0040,0554) | UI | 1 | Specimen (C.7.6.22) | 1 |  | Unique Identifier for Specimen. See Section C.7.6.22.1.2. |
| SpecimenTypeCodeSequence (nested) | (0040,059A) | SQ | 1 | Specimen (C.7.6.22) | 3 | SQ | Specimen Type. Only a single Item is permitted in this Sequence. |
| SpecimenShortDescription (nested) | (0040,0600) | LO | 1 | Specimen (C.7.6.22) | 3 |  | Short textual specimen description (may include ancestor specimen descriptions). |
| SpecimenDetailedDescription (nested) | (0040,0602) | UT | 1 | Specimen (C.7.6.22) | 3 |  | Detailed textual specimen description (may include ancestor specimen descriptions). |
| SpecimenPreparationSequence (nested) | (0040,0610) | SQ | 1 | Specimen (C.7.6.22) | 2 | SQ | Sequence of Items identifying the process steps used to prepare the specimen for image acquisition. This includes description of all processing necess... |
| SpecimenPreparationStepContentItemSequence (nested) | (0040,0612) | SQ | 1 | Specimen (C.7.6.22) | 1 | SQ | Sequence of Content Items identifying the processes used in one preparation step to prepare the specimen for image acquisition. One or more Items shal... |
| SpecimenLocalizationContentItemSequence (nested) | (0040,0620) | SQ | 1 | Specimen (C.7.6.22) | 1C | SQ | Sequence of Content Items identifying the location of the specimen in the container and/or in the image. See Section C.7.6.22.1.4. One or more Items s... |
| SpecimenLabelInImage | (0048,0010) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Indicates whether the specimen label is captured in the image. Enumerated Values: YES NO Shall be YES if Image Type (0008,0008) Value 3 is OVERVIEW or... |

### Acquisition-Device

| Keyword | Tag | VR | VM | Module | Type | Seq/Coded | Meaning (from table) |
|---|---|---|---|---|---|---|---|
| AcquisitionDateTime | (0008,002A) | DT | 1 | WSM Image (C.8.12.4) | 1 |  | The date and time that the acquisition of data that resulted in this image started. |
| AcquisitionDuration | (0018,9073) | FD | 1 | WSM Image (C.8.12.4) | 3 |  | Duration of the image acquisition in seconds. |
| AcquisitionDate | (0008,0022) | DA | 1 | General Acquisition (C.7.10.1) | 3 |  | The date the acquisition of data that resulted in this instance started. |
| AcquisitionTime | (0008,0032) | TM | 1 | General Acquisition (C.7.10.1) | 3 |  | The time the acquisition of data that resulted in this instance started. |
| Manufacturer | (0008,0070) | LO | 1 | Enhanced General Equipment (C.7.5.2) | 1 |  | Manufacturer of the equipment that produced the Composite Instances. |
| ManufacturerModelName | (0008,1090) | LO | 1 | Enhanced General Equipment (C.7.5.2) | 1 |  | Manufacturer's model name of the equipment that produced the Composite Instances. |
| DeviceSerialNumber | (0018,1000) | LO | 1 | Enhanced General Equipment (C.7.5.2) | 1 |  | Manufacturer's serial number of the equipment that produced the Composite Instances. |
| SoftwareVersions | (0018,1020) | LO | 1-n | Enhanced General Equipment (C.7.5.2) | 1 |  | Manufacturer's designation of software version of the equipment that produced the Composite Instances. See Section C.7.5.1.1.3. |
| UDISequence | (0018,100A) | SQ | 1 | General Equipment (C.7.5.1) | 3 | SQ | Unique Device Identifier (UDI) of the entire equipment. For example, the entire CT Scanner. Note Multiple Items may be present if the entire equipment... |
| UniqueDeviceIdentifier | (0018,1009) | UT | 1 | not in WSM IOD module tables checked | - |  | |
| InstitutionName | (0008,0080) | LO | 1 | General Equipment (C.7.5.1) | 3 |  | Institution where the equipment that produced the Composite Instances is located. Note This Attribute represents the organizational context only for t... |
| StationName | (0008,1010) | SH | 1 | General Equipment (C.7.5.1) | 3 |  | User defined name identifying the machine that produced the Composite Instances. |
| AcquisitionDeviceProcessingDescription | (0018,1400) | LO | 1 | WSM Image (C.8.12.4) | 3 |  | Description of visual processing performed on the image prior to exchange. Examples of this processing are: edge enhanced, gamma corrected, convolved ... |
| ConvolutionKernel | (0018,1210) | SH | 1-n | WSM Image (C.8.12.4) | 3 |  | Label for convolution kernel used in acquisition device visual processing. |
| AcquisitionContextSequence | (0040,0555) | SQ | 1 | Acquisition Context (C.7.6.14) | 2 | SQ | A Sequence of Items that describes the conditions present during the acquisition of the data of the SOP Instance. Zero or more Items shall be included... |
| DeviceUID | (0018,1002) | UI | 1 | General Equipment (C.7.5.1) | 3 |  | Unique identifier of the equipment that produced the Composite Instances. Note If present in an SR object, the value is expected to be the same as the... |

### Image-Characteristics

| Keyword | Tag | VR | VM | Module | Type | Seq/Coded | Meaning (from table) |
|---|---|---|---|---|---|---|---|
| ImageType | (0008,0008) | CS | 2-n | WSM Image (C.8.12.4) | 1 |  | Image identification characteristics. See Section C.8.12.4.1.1 for specialization. |
| SamplesPerPixel | (0028,0002) | US | 1 | WSM Image (C.8.12.4) | 1 |  | Number of samples (color planes) per Frame in this image. Enumerated Values: 3 1 See Section C.8.12.4.1.5 for further explanation. |
| PhotometricInterpretation | (0028,0004) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Specifies the intended interpretation of the pixel data. See Section C.8.12.4.1.5 for Enumerated Values. |
| PlanarConfiguration | (0028,0006) | US | 1 | WSM Image (C.8.12.4) | 1C |  | Indicates whether the pixel data are encoded color-by-plane or color-by-pixel. Required if Samples per Pixel (0028,0002) has a Value greater than 1. E... |
| NumberOfFrames | (0028,0008) | IS | 1 | WSM Image (C.8.12.4) | 1 |  | Number of Frames in the Multi-frame Image in this SOP Instance. Enumerated Values if Image Type (0008,0008) Value 3 is THUMBNAIL, LABEL or OVERVIEW: 1... |
| BitsAllocated | (0028,0100) | US | 1 | WSM Image (C.8.12.4) | 1 |  | Number of bits allocated for each pixel sample. Enumerated Values: 8 16 |
| BitsStored | (0028,0101) | US | 1 | WSM Image (C.8.12.4) | 1 |  | Number of bits stored for each pixel sample. Shall be equal to Bits Allocated (0028,0100). |
| HighBit | (0028,0102) | US | 1 | WSM Image (C.8.12.4) | 1 |  | Most significant bit for pixel sample data. High Bit (0028,0102) shall be one less than Bits Stored (0028,0101). |
| PixelRepresentation | (0028,0103) | US | 1 | WSM Image (C.8.12.4) | 1 |  | Data representation of pixel samples. Enumerated Values: 0 unsigned integer |
| LossyImageCompression | (0028,2110) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Specifies whether an Image has undergone lossy compression (at a point in its lifetime). Enumerated Values: 00 Image has not been subjected to lossy c... |
| LossyImageCompressionRatio | (0028,2112) | DS | 1-n | WSM Image (C.8.12.4) | 1C |  | Describes the approximate lossy compression ratio(s) that have been applied to this image. See Section C.7.6.1.1.5.2. Required if Lossy Image Compress... |
| LossyImageCompressionMethod | (0028,2114) | CS | 1-n | WSM Image (C.8.12.4) | 1C |  | A label for the lossy compression method(s) that have been applied to this image. See Section C.7.6.1.1.5.1. Required if Lossy Image Compression (0028... |
| VolumetricProperties | (0008,9206) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Indication if geometric manipulations are possible with Frames in the SOP Instance. See Section C.8.16.2.1.2. Enumerated Values: VOLUME pixels represe... |
| BurnedInAnnotation | (0028,0301) | CS | 1 | WSM Image (C.8.12.4) | 1 |  | Indicates whether or not image contains sufficient burned in annotation to identify the patient. Enumerated Values: YES NO Note If Specimen Label in I... |
| RescaleIntercept | (0028,1052) | DS | 1 | WSM Image (C.8.12.4) | 1C |  | The value b in relationship between stored values (SV) and the output units. Output units = m*SV + b. Required if Photometric Interpretation (0028,000... |
| RescaleSlope | (0028,1053) | DS | 1 | WSM Image (C.8.12.4) | 1C |  | m in the equation specified by Rescale Intercept (0028,1052). Required if Photometric Interpretation (0028,0004) is MONOCHROME2. Enumerated Values: 1 |
| PresentationLUTShape | (2050,0020) | CS | 1 | WSM Image (C.8.12.4) | 1C |  | Specifies an identity transformation for the Presentation LUT, such that the output of all grayscale transformations defined in the IOD containing thi... |
| RecommendedAbsentPixelCIELabValue | (0048,0015) | US | 3 | WSM Image (C.8.12.4) | 3 |  | A color triplet value with which it is recommended to display the pixels of the Total Pixel Matrix that are not encoded. The units are specified in PC... |
| RecognizableVisualFeatures | (0028,0302) | CS | 1 | General Image (C.7.6.1) | 3 |  | Indicates whether or not the image contains sufficiently recognizable visual features to allow the image or a reconstruction from a set of images to i... |

### PHI-Identity

| Keyword | Tag | VR | VM | Module | Type | Seq/Coded | Meaning (from table) |
|---|---|---|---|---|---|---|---|
| PatientName | (0010,0010) | PN | 1 | Patient (C.7.1.1) | 2 |  | Patient's full name. |
| PatientID | (0010,0020) | LO | 1 | Patient (C.7.1.1) | 2 |  | Primary identifier for the Patient. Note In the case of imaging a group of small animals simultaneously, the single Value of this identifier correspon... |
| PatientBirthDate | (0010,0030) | DA | 1 | Patient (C.7.1.1) | 2 |  | Birth date of the Patient. |
| PatientBirthTime | (0010,0032) | TM | 1 | Patient (C.7.1.1) | 3 |  | Birth time of the Patient. |
| PatientSex | (0010,0040) | CS | 1 | Patient (C.7.1.1) | 2 |  | Sex of the named Patient. Enumerated Values: M male F female O other See Note 2 and Note 3. |
| OtherPatientNames | (0010,1001) | PN | 1-n | Patient (C.7.1.1) | 3 |  | Other names used to identify the Patient. |
| OtherPatientIDsSequence | (0010,1002) | SQ | 1 | Patient (C.7.1.1) | 3 | SQ | A Sequence of identification numbers or codes used to identify the Patient, which may or may not be human readable, and may or may not have been obtai... |
| PatientComments | (0010,4000) | LT | 1 | Patient (C.7.1.1) | 3 |  | User-defined additional information about the Patient. |
| PatientIdentityRemoved | (0012,0062) | CS | 1 | Patient (C.7.1.1) | 3 |  | The true identity of the Patient has been removed from the Attributes and the Pixel Data Enumerated Values: YES NO |
| DeidentificationMethod | (0012,0063) | LO | 1-n | Patient (C.7.1.1) | 1C |  | A description or label of the mechanism or method use to remove the Patient's identity. May be multi-valued if successive de-identification steps have... |
| DeidentificationMethodCodeSequence | (0012,0064) | SQ | 1 | Patient (C.7.1.1) | 1C | SQ | A code describing the mechanism or method use to remove the Patient's identity. One or more Items shall be included in this Sequence. Multiple Items a... |
| StudyInstanceUID | (0020,000D) | UI | 1 | General Study (C.7.2.1) | 1 |  | Unique identifier for the Study. |
| StudyDate | (0008,0020) | DA | 1 | General Study (C.7.2.1) | 2 |  | Date the Study started. |
| StudyTime | (0008,0030) | TM | 1 | General Study (C.7.2.1) | 2 |  | Time the Study started. |
| AccessionNumber | (0008,0050) | SH | 1 | General Study (C.7.2.1) | 2 |  | A departmental Information System generated number that identifies the Imaging Service Request. |
| StudyID | (0020,0010) | SH | 1 | General Study (C.7.2.1) | 2 |  | User or equipment generated Study identifier. |
| ReferringPhysicianName | (0008,0090) | PN | 1 | General Study (C.7.2.1) | 2 |  | Name of the Patient's referring physician. |
| ImageComments | (0020,4000) | LT | 1 | General Image (C.7.6.1) | 3 |  | User-defined comments about the image. |
| SeriesDate | (0008,0021) | DA | 1 | General Series (C.7.3.1) | 3 |  | Date the Series started. |
| PerformingPhysicianName | (0008,1050) | PN | 1-n | General Series (C.7.3.1) | 3 |  | Name of the physician(s) administering the Series. |
| OperatorsName | (0008,1070) | PN | 1-n | General Series (C.7.3.1) | 3 |  | Name(s) of the operator(s) supporting the Series. |
| SeriesDescription | (0008,103E) | LO | 1 | General Series (C.7.3.1) | 3 |  | Description of the Series. |
| SpecimenDescriptionSequence | (0040,0560) | SQ | 1 | Specimen (C.7.6.22) | 1 | SQ | Sequence of identifiers and detailed description of the specimen(s) being imaged. One or more Items shall be included in this Sequence. Each specimen ... |
| AcquisitionContextSequence | (0040,0555) | SQ | 1 | Acquisition Context (C.7.6.14) | 2 | SQ | A Sequence of Items that describes the conditions present during the acquisition of the data of the SOP Instance. Zero or more Items shall be included... |

"(nested)" means the attribute is inside a sequence item (for example inside Optical Path Sequence or Specimen Description Sequence).

## Flattening rules needed for I2S

I2S stores flat text, so the sequence and coded attributes need a rule:

1. **Optical Path Sequence (0048,0105)** is one item per optical path, type 1 in this IOD. Items carry type 1 children: Optical Path Identifier (0048,0106) and Illumination Type Code Sequence (0022,0016). Flatten as `OpticalPath[<id>].<child>`. Only the first Item is needed for single-path WSI.
2. **Code sequences** (Illuminator Type, Illumination Color, Light Path Filter stacks, Lenses, Channel Description, Container Type, Specimen Type, Primary Anatomic Structure) use Table 8.8-1. Flatten to the Code Meaning text, or to `Value|Scheme|Meaning`, and state which in the I2S spec. Do not store code values without their scheme.
3. **Specimen Description Sequence (0040,0560)**, type 1, with Specimen Identifier (0040,0551) and Specimen UID (0040,0554), both type 1. Preparation steps (0040,0610) are a sequence of content-item sequences (BTID 8001), which is the only place stain information lives in the standard. Flatten as ordered step text. Stain names are not codes in this pass (see Unverified).
4. **UDI Sequence (0018,100A)** is the only UDI attribute in the IOD (see Comparison). Flatten to the UDI text of the first item.
5. **Total Pixel Matrix Origin Sequence (0048,0008)** and **Plane Position (Slide) Sequence (0048,021A)** carry X/Y/Z offsets. Use the first item for slide origin; per-frame positions are not flat-storable.
6. **Dimension Index Sequence / Functional Group Pointer** (C.7.6.17) are internal indexing; do not store.

## Groups for I2S

The groups are the ones requested. Attributes can appear under more than one heading when a single attribute serves two purposes.

Optics: Optical Path Module attributes (Objective Lens Power, Objective Lens Numerical Aperture, Condenser Lens Power, Illumination, Light Path Filter, Image Path Filter, Lenses, ICC Profile), Pixel Spacing and Slice Thickness from the Pixel Measures macro, and the Total Pixel Matrix geometry from the Tile Organization module. Magnification is not stored directly: Objective Lens Power is the nominal objective power. Pixel Spacing is the µm-per-pixel source (in mm, so multiply by 1000 for µm).

Focus/Z: Focus Method, Extended Depth of Field, Number of Focal Planes, Distance Between Focal Planes, Total Pixel Matrix Focal Planes, Spacing Between Slices, Imaged Volume Depth, Z Offset in Slide Coordinate System, Dimension Organization Type.

Specimen and stain: Container Identifier, Specimen Description Sequence, Specimen Identifier, Specimen Preparation Sequence, Specimen Label in Image.

Acquisition and device: Acquisition DateTime, Acquisition Duration, Manufacturer, Model, Device Serial, Software Versions, UDI Sequence, Institution Name, Station Name, Processing Description, Convolution Kernel, Acquisition Context Sequence.

Image characteristics: Image Type, Photometric, Samples per Pixel, Planar Configuration, Bits, Lossy Compression (three attributes), Volumetric Properties, Burned In Annotation, Rescale, Presentation LUT Shape, Recommended Absent Pixel CIELab Value, ICC Profile and Color Space (in the optical path item).

## Comparison with the existing I2S v0.1 keys

| I2S key | DICOM attribute | IOD treatment | Action |
|---|---|---|---|
| DigitalImageIdentifier | none by that name; probably SOP Instance UID (0008,0018), type 1 in C.12.1 | Not verified in this pass; C.12.1 is in PS3.3 sect_C.12.html (not checked for the exact row) | Map to SOP Instance UID if that is what it holds. Confirm. |
| DigitalImageIdentifierIsPHI | no DICOM attribute | Closest is Burned In Annotation (0028,0301) and Specimen Label in Image (0048,0010) | Keep as an I2S-only flag; define it from Burned In Annotation. |
| Manufacturer (0008,0070) | LO, VM 1 | General Equipment C.7.5.1 Type 2; Enhanced General Equipment C.7.5.2 Type 1 | The IOD requires it (Type 1 via C.7.5.2). Keep. |
| ManufacturerModelName (0008,1090) | LO, VM 1 | C.7.5.2 Type 1; C.7.5.1 Type 3 | Keep. Type 1 in this IOD. |
| DeviceSerialNumber (0018,1000) | LO, VM 1 | C.7.5.2 Type 1; C.7.5.1 Type 3 | Keep. Type 1 in this IOD. |
| SoftwareVersions (0018,1020) | LO, VM 1-n | C.7.5.2 Type 1; C.7.5.1 Type 3 | Keep. Multi-valued; I2S needs a joining rule. |
| UniqueDeviceIdentifier (0018,1009) | UT, VM 1 (PS3.6) | **Not in any module of this IOD** (not in C.7.5.1 or C.7.5.2). The IOD's UDI attribute is UDI Sequence (0018,100A) (SQ, Type 3, C.7.5.1). | Do not use 0018,1009 for WSI. Replace with UDI Sequence flattened, or drop it. |
| AcquisitionDateTime (0008,002A) | DT, VM 1 | WSM Image Module C.8.12.4 Type 1; General Acquisition C.7.10.1 Type 3 | Keep. Type 1 here. |

Attributes the IOD defines that I2S does not yet have, most useful for optics and specimen identity: ObjectiveLensPower (0048,0112), ObjectiveLensNumericalAperture (0048,0113), PixelSpacing (0028,0030), SliceThickness (0018,0050), SpacingBetweenSlices (0018,0088), TotalPixelMatrixColumns/Rows (0048,0006/0007), TotalPixelMatrixFocalPlanes (0048,0303), FocusMethod (0048,0011), ExtendedDepthOfField (0048,0012), NumberOfFocalPlanes (0048,0013), DistanceBetweenFocalPlanes (0048,0014), ContainerIdentifier (0040,0512), SpecimenIdentifier (0040,0551), SpecimenLabelInImage (0048,0010), ImageType (0008,0008), BurnedInAnnotation (0028,0301), LossyImageCompression (0028,2110), ImageOrientationSlide (0048,0102).

## PHI and identity risk

Attributes that identify a patient directly or through linkage. "Type" is the IOD requirement.

- **Direct patient identity (module M in this IOD):** PatientName (0010,0010) Type 2; PatientID (0010,0020) Type 2; PatientBirthDate (0010,0030) Type 2; PatientBirthTime (0010,0032) Type 3; PatientSex (0010,0040) Type 2; OtherPatientNames (0010,1001) Type 3; OtherPatientIDsSequence (0010,1002) Type 3; PatientComments (0010,4000) Type 3 (free text). Patient Identity Removed (0012,0062) and De-identification Method (0012,0063/0064) record de-identification; they are the attributes that show whether the instance was de-identified.
- **Study-level linkage:** StudyDate (0008,0020) Type 2; StudyTime (0008,0030) Type 2; AccessionNumber (0008,0050) Type 2 (departmental order ID, links to the patient); StudyID (0020,0010) Type 2; ReferringPhysicianName (0008,0090) Type 2; StudyInstanceUID (0020,000D) Type 1 (unique, links records).
- **Series-level:** SeriesDate (0008,0021) Type 3; PerformingPhysicianName (0008,1050) Type 3; OperatorsName (0008,1070) Type 3; SeriesDescription (0008,103E) Type 3 (free text).
- **Dates:** AcquisitionDateTime (0008,002A) Type 1 is a date-of-service identifier under HIPAA-style rules; I2S should treat it as PHI-adjacent (it is the same date as StudyDate in most workflows).
- **Image-level:** BurnedInAnnotation (0028,0301) Type 1: YES means the pixels show enough to identify the patient. This is the authoritative PHI signal for the pixel data. ImageComments (0020,4000) Type 3 is free text and may contain identifiers.
- **Specimen identifiers (not patient fields, but can encode MRN or accession):** ContainerIdentifier (0040,0512) Type 1; SpecimenIdentifier (0040,0551) Type 1; SpecimenDetailedDescription (0040,0602) Type 3 (free text, may name the patient or relative). The standard says Specimen Identifier should not be parsed to recover an accession number (C.7.6.22.1.1), which supports storing it as opaque.
- **Institution and device (quasi-identifier):** InstitutionName (0008,0080) Type 3; StationName (0008,1010) Type 3; DeviceSerialNumber (0018,1000) is not patient PHI but identifies the scanner.

Non-PHI but sensitive to the lab: Specimen Label in Image (0048,0010) YES means the label is in the pixels (it may carry identifiers that are not patient fields).

## Unverified or not checked in this pass

- C.12.1 SOP Instance UID row and exact requirement type: not read from the chunk page.
- SOP Class UID value 1.2.840.10008.5.1.4.1.1.77.1.6: not confirmed on any page fetched (PS3.4 Annex B not read).
- Stain and prep codes: the standard uses BTID 8001 "Specimen Preparation" content items (Table 10-2). The coded values for hematoxylin, eosin and other stains (SNOMED or other scheme) were not fetched from PS3.16 and are not stated here.
- Primary Anatomic Structure macro (Table 10-8, inside Specimen Description Sequence): listed in C.7.6.22 but its item attributes were not extracted.
- Conditions in parentheses for types 1C/2C (for example Image Orientation (Slide) and Pixel Spacing) were read from the table text, not from the full condition text.
- Patient module rows came from the C.7 chapter page and the Patient Module table (sect_C.7.html). Values are PS3.6 VR/VM; the IOD usage is M.
- Multi-frame Dimension and General Image rows were read from chapter pages, not the individual module pages (sect_C.7.6.1.html and C.7.1.1.html return 404; the chapter files are sect_C.7.6.html and sect_C.7.html).
