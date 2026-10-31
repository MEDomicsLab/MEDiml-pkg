Input Data
==========

``MEDiml`` package accepts two formats of input data: `NIfTI <https://brainder.org/2012/09/23/the-nifti-file-format/>`__ 
and `DICOM <https://fr.wikipedia.org/wiki/Digital_imaging_and_communications_in_medicine>`__. Each format has its own conventions
that need to be followed. The following sections describe the norms and the conventions for each format and we recommend you process your 
dataset in a way that respects them.

DICOM
-----

A. **Image**

  Every DICOM file contains a header and a body. The header contains the metadata of the image, and the body contains the image itself.
  The header contains information about the scan and the most important for our package is the following:

  - **Patient ID**: Primary identifier for the Patient, referenced in the ``(0010,0020) PatientID`` field of the header. This field should not 
    contain any underscore and for compatibility with other `MEDomics packages <https://github.com/medomics>`__, we recommend using the following 
    format: ``'study-institution-numericID'``. For example, ``'STS-McGill-001'``. It is also used in the :doc:`../csv_file` of the dataset under 
    the column ``PatientID``.
  - **Series description**: Referenced in the ``(0008,103E) Series Description`` field of the DICOM header. A description of the series, usually describes 
    the type of the modality used. This field must be renamed to be the same for each sequence of each modality. For example, ``'T1'`` for all the 
    T1-weighted MRI scans and ``'T2'`` for all the T2-weighted MRI scans. It is referred to in the :doc:`../csv_file` of the dataset as ``ImagingScanName``.

B. **RTstruct**

  RTstruct files define the area of significance and hold information about each region of interest (ROI). The RTstruct files are associated with their
  imaging volume using the ``(0020,000E) Series Instance UID`` or the ``(0020,0052) Frame of Reference UID`` found in the file's header. 
  ``MEDiml`` package recommends the following:

  - **Patient ID**: Same conventions and recommendations as the DICOM image.
  - **Series description**: Same conventions and recommendations as the DICOM image.
  - **ROI name**: Only found in DICOM RTstruct files and referenced in each element (each ROI) of the ``(3006,0020) Structure Set ROI Sequence`` list of 
    the DICOM header, under the attribute ``(3006,0026) ROI Name`` which is a name given to each region of interest (ROI). ``MEDiml`` has no 
    conventions over this field, but we recommend renaming each ROI name in a simple and logic way to differentiate them from each other. It is very 
    important to keep track of all the ROIs in your dataset since they need to be specified in the :doc:`../csv_file` of the dataset under the 
    ``ROIName`` column to be used later in your radiomics analysis.

NIfTI
-----

The NIfTI format is a simple format that only contains the image itself. Unlike DICOM, the NIfTI format does contain any
information about the regions of interest (ROI) so it needs to be provided in other separate files. In order for ``MEDMEDimlimage`` to read a NIfTI scan
files, they need to be put in the same folder with the following names:

- ``'PatientID__SeriesDescription(ROILabel).Modality.nii.gz'``: The image itself. For example: ``'STS-McGill-001__T1(GTV).MRscan.nii.gz'``.
- ``'PatientID__SeriesDescription(ROIname).ROI.nii.gz'``: The ROI or the mask of the image. This file should contain a binary mask of the ROI. 
  For example: ``'STS-McGill-001__T1(GTV_Mass).ROI.nii.gz'``.

The following figure sums up the ``MEDiml`` logic in reading data for both formats:

.. image:: /figures/InputDataSummary.png
    :width: 1000
    :align: center

If these conventions are followed, the ``DataManager`` class will be able to read the data and create the ``MEDscan`` objects that will be used
in the radiomics analysis with no further intervention from the user. For instance, ``MEDiml`` package is capable of automatically updating 
the fields of all the DICOM files as long as the dataset is organized in the following way:
::

    dataset_folder
    ├── Patient ID 1
    │   ├── Modality 1
    │   │   ├── ImagingScanName 1
    │   │   │   ├── images
    │   │   │   │   └── DICOM files
    │   │   │   └── masks
    │   │   │       └── DICOM files
    │   │   └── ImagingScanName 2
    │   │       └── ...
    │   └── Modality 2
    │       └── ...
    ├── Patient ID 2
    │   └── ...
    └── ...

Each patient folder contains one folder per imaging modality (``MRI``, ``CT``, ``PET`` or ``ADC``), which contains one folder
per imaging scan (the MRI sequence, for example ``T1``). Each imaging scan folder separates its files in two sub-folders:

- ``images``: The DICOM files of the imaging volume (one file per slice).
- ``masks``: The DICOM files defining the regions of interest of the imaging volume (RTstruct or SEG files).

For example:

::

    dataset_folder
    ├── STS-McGill-001
    │   ├── MRI
    │   │   ├── T1
    │   │   │   ├── images
    │   │   │   │   └── *.dcm
    │   │   │   └── masks
    │   │   │       └── *.dcm
    │   │   └── T2FS
    │   │       ├── images
    │   │       │   └── *.dcm
    │   │       └── masks
    │   │           └── *.dcm
    │   └── PET
    │       ├── images
    │       │   └── *.dcm
    │       └── masks
    │           └── *.dcm
    ├── STS-McGill-002
    │   └── CT
    │       ├── images
    │       │   └── *.dcm
    │       └── masks
    │           └── *.dcm
    └── ...

Some levels of this structure can be omitted:

- **Unknown sequence**: if the sequence of an imaging scan is unknown (no ``SeriesDescription``), the modality folder is enough and
  holds the files of the scan directly, like the ``PET`` folder of ``STS-McGill-001`` above. The imaging scan is then named after its
  modality (``ImagingScanName`` is ``PET`` in the :doc:`../csv_file`). This only applies if the patient has a single scan of this
  modality, otherwise each scan gets its own folder (named after the modality, ``PET-2``, etc. if needed).
- **Images and masks not separated**: if the masks cannot be told apart from the images, all the DICOM files can be put directly in
  the imaging scan folder (or the modality folder if the sequence is unknown). The other DICOM files that are neither images nor masks
  (for example RTdose files) are also put there.

Just run the following command: ::

  python scripts/organize_dataset.py --path-dataset path/to/your/dataset/folder

If your dataset is not organized this way yet, the script will organize it for you: all the DICOM files found in the dataset folder
(and its sub-folders) are grouped by ``PatientID``, modality and imaging scan (``SeriesInstanceUID``), and copied to a new folder
following the structure above (``path/to/your/dataset/folder_organized`` by default, use ``--path-save`` to change it). The original
dataset is not modified. The modality folders are named after the DICOM ``Modality`` field (``MR`` becomes ``MRI`` and ``PT`` becomes
``PET``) and each imaging scan folder is named after the scan's ``SeriesDescription``. The imaging files are copied in the ``images``
sub-folder, and the RTstruct and SEG files are copied in the ``masks`` sub-folder of the imaging scan they reference. In both cases,
the ``PatientID`` and ``SeriesDescription`` fields of the DICOM headers are then updated using the names of the patient and imaging scan
folders (or the modality folder if the sequence is unknown). ::

  python scripts/organize_dataset.py --path-dataset path/to/your/dataset/folder --path-save path/to/the/organized/dataset
