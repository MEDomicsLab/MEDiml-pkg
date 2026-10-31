# Changelog

All notable changes to MEDiml are documented in this file. The versions of MEDiml are published on
[PyPI](https://pypi.org/project/mediml/#history).

## [Unreleased]

### Changed
- DICOM datasets are now organized as `PatientID/Modality/ImagingScanName/{images,masks}/*.dcm`
  (`scripts/organize_dataset.py`), and are read accordingly by the pre-radiomics checks and the batch extraction.
- The ROI CSV generator (`scripts/generate_roi_csv.py`) supports the new DICOM dataset organization.
- The supported Python versions are now 3.8, 3.9 and 3.10 (all 3.10.x releases).

### Added
- Automatic categorization of the extracted features by complexity level after batch extraction.
- JOSS paper draft, contributing guidelines, code of conduct and citation metadata.

### Fixed
- The DICOM mode of the ROI CSV generator, which failed when storing the ROI names.

## [0.19.1]

Latest version published on PyPI.
