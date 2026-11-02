Limitations and future work
===========================

This section lists the current limitations of ``MEDiml`` and the features planned for future releases.

Data formats
------------

- Only the DICOM and NIfTI formats are currently supported. Support for the NRRD format will be added in future releases.
- A mask cannot be loaded when its format differs from the format of the image, for example when the image is in DICOM
  and the mask is in NIfTI. The image and its mask must therefore be in the same format. This will be fixed in future
  releases.

Learning
--------

- The data can currently be split using random subsampling, cross-validation or by institution. Bootstrapping and
  leave-one-out cross-validation (LOOCV) will be added in future releases.

If you need one of these features or encounter another limitation, feel free to open an issue on
`GitHub <https://github.com/MEDomicsLab/MEDiml-pkg/issues>`__.
