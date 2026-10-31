#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from typing import Union

# Sub-folders separating the imaging volumes from the masks in each imaging scan folder
# of an organized DICOM dataset (must match the names used in scripts/organize_dataset.py).
DICOM_IMAGES_FOLDER = 'images'
DICOM_MASKS_FOLDER = 'masks'


def get_dicom_scan_dir(path_file: Union[str, Path]) -> Path:
    """Returns the folder of the imaging scan a DICOM file belongs to, in a DICOM dataset organized as
    ``PatientID/Modality/ImagingScanName/{images,masks}/*.dcm`` (``PatientID/Modality/{images,masks}/*.dcm``
    if the sequence is unknown). The images and masks sub-folders are optional.

    Args:
        path_file (Union[str, Path]): Path to the DICOM file.

    Returns:
        Path: The folder of the file, or its parent if the file is in the images or masks sub-folder.
    """
    path_file = Path(path_file)
    if path_file.parent.name in (DICOM_IMAGES_FOLDER, DICOM_MASKS_FOLDER):
        return path_file.parent.parent
    return path_file.parent


def is_dicom_scan_dir(path_dir: Union[str, Path]) -> bool:
    """Checks if a folder holds the files of an imaging scan, directly or in its images or masks sub-folders.

    Args:
        path_dir (Union[str, Path]): Path to the folder.

    Returns:
        bool: True if the folder is an imaging scan folder.
    """
    path_dir = Path(path_dir)
    return path_dir.is_dir() and (
        any(path_dir.glob('*.dcm'))
        or (path_dir / DICOM_IMAGES_FOLDER).is_dir()
        or (path_dir / DICOM_MASKS_FOLDER).is_dir()
    )


def find_dicom_scan_dir(path_dataset: Union[str, Path], patient_id: str, scan_name: str) -> Union[Path, None]:
    """Finds the folder of an imaging scan in an organized DICOM dataset: ``PatientID/Modality/ImagingScanName``,
    or ``PatientID/ImagingScanName`` for a scan of unknown sequence put directly in its modality folder.

    Args:
        path_dataset (Union[str, Path]): Path to the DICOM dataset.
        patient_id (str): Patient ID (name of the patient folder).
        scan_name (str): Imaging scan name (name of the sequence folder, or of the modality folder
            if the sequence is unknown).

    Returns:
        Union[Path, None]: The imaging scan folder, None if not found.
    """
    path_patient = Path(path_dataset) / patient_id
    if not path_patient.is_dir():
        return None
    candidates = [path_patient / scan_name]
    candidates += [d / scan_name for d in sorted(path_patient.iterdir()) if d.is_dir()]
    for candidate in candidates:
        if candidate.name not in (DICOM_IMAGES_FOLDER, DICOM_MASKS_FOLDER) and is_dicom_scan_dir(candidate):
            return candidate
    return None
