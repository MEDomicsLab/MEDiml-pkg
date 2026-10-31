import argparse
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path
from typing import List, Union

import pydicom
import pydicom.misc
from tqdm import tqdm

# Imaging modalities handled by MEDiml and the name of their folder in the organized dataset.
# All the other DICOM files (RTSTRUCT, RTDOSE...) are associated to the imaging scan they reference.
MODALITY_FOLDERS = {'MR': 'MRI', 'CT': 'CT', 'PT': 'PET', 'ADC': 'ADC'}
IMAGING_MODALITIES = list(MODALITY_FOLDERS)
# Segmentation modalities, copied in the masks sub-folder of the imaging scan they reference.
# The other non-imaging files (RTDOSE, RTPLAN...) are copied in the imaging scan folder itself.
MASK_MODALITIES = ['RTSTRUCT', 'SEG']
# Sub-folders separating the imaging volumes from the masks in each imaging scan folder
# (must match the names used in MEDiml/utils/dicom_dataset.py).
IMAGES_FOLDER = 'images'
MASKS_FOLDER = 'masks'


def sanitize_name(name: str) -> str:
    """Removes the characters that cannot be used in a folder name or in a MEDiml name.

    Args:
        name(str): Name to sanitize.

    Returns:
        str: The sanitized name.
    """
    name = re.sub(r'[\\/:*?"<>|()&_\s]+', '-', str(name).strip())
    return name.strip('-.') or 'Unknown'


def get_sequence_name(header: pydicom.Dataset) -> Union[str, None]:
    """Returns the sequence name of an imaging scan, read from its SeriesDescription.

    Args:
        header(pydicom.Dataset): Header of a DICOM file of the imaging scan.

    Returns:
        Union[str, None]: The sanitized sequence name, None if the sequence is unknown.
    """
    sequence = sanitize_name(getattr(header, 'SeriesDescription', '') or '')
    if sequence in ('Unknown', MODALITY_FOLDERS[str(header.Modality)]):
        return None
    if sequence.lower() in (IMAGES_FOLDER, MASKS_FOLDER):
        # Avoids confusing the sequence folder with the images and masks sub-folders
        sequence += '-scan'
    return sequence


def get_scan_dir(file: Path) -> Path:
    """Returns the folder of the imaging scan a DICOM file belongs to.

    Args:
        file(Path): Path to the DICOM file.

    Returns:
        Path: The folder of the file, or its parent if the file is in the images or masks sub-folder.
    """
    return file.parent.parent if file.parent.name in (IMAGES_FOLDER, MASKS_FOLDER) else file.parent


def is_organized(path_dataset: Path, dicom_files: List[Path]) -> bool:
    """Checks if the dataset is already organized as "path_dataset/PatientID/Modality/Sequence/{images,masks}/*.dcm"
    (or "path_dataset/PatientID/Modality/{images,masks}/*.dcm" if the sequence is unknown), with a single imaging
    series per scan folder.

    Args:
        path_dataset(Path): Path to the dataset.
        dicom_files(List[Path]): All the DICOM files of the dataset.

    Returns:
        bool: True if the dataset is already organized.
    """
    series_per_scan = defaultdict(set)
    for file in dicom_files:
        # MEDiml only reads the DICOM files with a ".dcm" extension
        parts = file.relative_to(path_dataset).parts
        if file.suffix != '.dcm' or len(parts) < 3 or parts[1] not in MODALITY_FOLDERS.values():
            return False
        scan_dir = get_scan_dir(file)
        if len(scan_dir.relative_to(path_dataset).parts) not in (2, 3):
            return False
        header = pydicom.dcmread(str(file), stop_before_pixels=True, force=True)
        modality = str(getattr(header, 'Modality', ''))
        if modality in IMAGING_MODALITIES:
            if file.parent.name == MASKS_FOLDER:
                return False
            series_per_scan[scan_dir].add(header.SeriesInstanceUID)
        elif modality in MASK_MODALITIES and file.parent.name == IMAGES_FOLDER:
            return False
    # A modality folder cannot hold the files of an imaging scan and other imaging scan folders
    if any(scan_dir.parent in series_per_scan for scan_dir in series_per_scan):
        return False
    return all(len(series) == 1 for series in series_per_scan.values())


def get_referenced_series_uid(header: pydicom.Dataset) -> Union[str, None]:
    """Returns the Series Instance UID of the imaging scan referenced by an RTSTRUCT file.

    Args:
        header(pydicom.Dataset): Header of the RTSTRUCT file.

    Returns:
        Union[str, None]: The referenced Series Instance UID, None if not found.
    """
    try:
        return header.ReferencedFrameOfReferenceSequence[
            0].RTReferencedStudySequence[
            0].RTReferencedSeriesSequence[
            0].SeriesInstanceUID
    except (AttributeError, IndexError):
        return None


def get_frame_of_reference_uid(header: pydicom.Dataset) -> Union[str, None]:
    """Returns the Frame of Reference UID of a DICOM file.

    Args:
        header(pydicom.Dataset): Header of the DICOM file.

    Returns:
        Union[str, None]: The Frame of Reference UID, None if not found.
    """
    if 'FrameOfReferenceUID' in header:
        return header.FrameOfReferenceUID
    try:
        return header.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
    except (AttributeError, IndexError):
        return None


def organize(path_save: Path, dicom_files: List[Path]) -> None:
    """Copies all the DICOM files of the dataset in "path_save/PatientID/Modality/Sequence/",
    one folder per imaging scan (Series Instance UID). The imaging files are copied in the "images"
    sub-folder and the masks (RTSTRUCT, SEG) in the "masks" sub-folder of the imaging scan they reference.
    The other non-imaging files (RTDOSE...) are copied in the imaging scan folder itself.

    If the sequence of a scan is unknown (no SeriesDescription), the scan is named after its modality and
    its files are put directly in the modality folder, unless the patient has other scans of this modality.

    Args:
        path_save(Path): Path where to save the organized dataset.
        dicom_files(List[Path]): All the DICOM files of the dataset.

    Returns:
        None.
    """
    images = defaultdict(list)  # Series Instance UID -> DICOM files
    series_info = {}            # Series Instance UID -> (PatientID, modality folder, sequence, Frame of Reference UID)
    others = []                 # (DICOM file, header) of the non-imaging files
    print('--> Reading all the DICOM headers')
    for file in tqdm(dicom_files):
        try:
            header = pydicom.dcmread(str(file), stop_before_pixels=True, force=True)
        except Exception as e:
            print(f'Error while reading: {file}, error: {e}')
            continue
        modality = str(getattr(header, 'Modality', ''))
        if modality in IMAGING_MODALITIES:
            series_uid = header.SeriesInstanceUID
            images[series_uid].append(file)
            if series_uid not in series_info:
                series_info[series_uid] = (
                    sanitize_name(getattr(header, 'PatientID', '') or 'Unknown'),
                    MODALITY_FOLDERS[modality],
                    get_sequence_name(header),
                    get_frame_of_reference_uid(header)
                )
        else:
            others.append((file, header))

    # Name the scan folders, a number is added if a patient has many scans with the same name
    scans_per_modality = defaultdict(list)
    for series_uid, (patient_id, modality_folder, sequence, _) in series_info.items():
        scans_per_modality[(patient_id, modality_folder)].append((sequence or modality_folder, series_uid))
    scan_dirs = {}
    for (patient_id, modality_folder), scans in scans_per_modality.items():
        path_modality = path_save / patient_id / modality_folder
        if len(scans) == 1 and series_info[scans[0][1]][2] is None:
            # Single scan of unknown sequence, the modality folder is enough
            scan_dirs[scans[0][1]] = path_modality
            continue
        names_used = defaultdict(int)
        for scan_name, series_uid in sorted(scans):
            names_used[scan_name] += 1
            count = names_used[scan_name]
            scan_dirs[series_uid] = path_modality / (scan_name if count == 1 else f'{scan_name}-{count}')

    # Associate the non-imaging files to their imaging scan
    files_to_copy = [(file, scan_dirs[uid] / IMAGES_FOLDER) for uid, files in images.items() for file in files]
    for file, header in others:
        series_uid = get_referenced_series_uid(header)
        if series_uid not in scan_dirs:
            # Fall back on the Frame of Reference UID, only if it identifies a single scan
            frame_uid = get_frame_of_reference_uid(header)
            matches = [uid for uid, info in series_info.items() if frame_uid and info[3] == frame_uid]
            series_uid = matches[0] if len(matches) == 1 else None
        if series_uid is None:
            print(f'Could not associate {file} ({getattr(header, "Modality", "Unknown modality")}) '
                  'to a single imaging scan, it will be ignored.')
            continue
        if str(getattr(header, 'Modality', '')) in MASK_MODALITIES:
            files_to_copy.append((file, scan_dirs[series_uid] / MASKS_FOLDER))
        else:
            # Neither an image nor a mask, kept in the imaging scan folder
            files_to_copy.append((file, scan_dirs[series_uid]))

    # Copy the files, named after their SOP Instance UID with a ".dcm" extension (required by MEDiml)
    print(f'--> Copying the DICOM files of {len(scan_dirs)} imaging scan(s) to {path_save}')
    for file, folder in tqdm(files_to_copy):
        folder.mkdir(parents=True, exist_ok=True)
        header = pydicom.dcmread(str(file), stop_before_pixels=True, force=True)
        name = getattr(header, 'SOPInstanceUID', '') or file.stem
        shutil.copy2(file, folder / f'{name}.dcm')


def update_headers(path_dataset: Path) -> None:
    """Updates the PatientID and the SeriesDescription of all the DICOM files of an organized dataset
    using the names of the patient and imaging scan folders (the modality folder if the sequence is unknown).

    Args:
        path_dataset(Path): Path to the organized dataset.

    Returns:
        None.
    """
    print('--> Updating the DICOM headers')
    for file in tqdm(sorted(path_dataset.rglob('*.dcm'))):
        dicom_header = pydicom.dcmread(str(file))
        dicom_header.PatientID = file.relative_to(path_dataset).parts[0]
        if 'SeriesDescription' in dicom_header:
            dicom_header.SeriesDescription = os.path.basename(get_scan_dir(file))
        dicom_header.save_as(str(file))


def main(path_dataset: Union[str, Path], path_save: Union[str, Path] = None) -> None:
    """Process the dataset to follow the MEDiml conventions:
    "dataset_folder/PatientID/Modality/Sequence/{images,masks}/*.dcm".

    If the dataset is not organized yet, the files are copied (the original dataset is not modified)
    in ``path_save`` following this structure. The PatientID and SeriesDescription fields of the
    DICOM headers are then updated using the names of the patient and imaging scan folders.

    Args:
        path_dataset(Union[str, Path]): Path to the dataset.
        path_save(Union[str, Path], optional): Path where to save the organized dataset. Only used if the
            dataset is not organized. Defaults to "<path_dataset>_organized".

    Returns:
        None.
    """
    path_dataset = Path(path_dataset)
    if not path_dataset.is_dir():
        raise ValueError(f'The dataset folder does not exist: {path_dataset}')
    dicom_files = sorted(f for f in path_dataset.rglob('*') if f.is_file() and pydicom.misc.is_dicom(f))
    if not dicom_files:
        raise ValueError(f'No DICOM file was found in: {path_dataset}')

    if is_organized(path_dataset, dicom_files):
        print(f'--> The dataset is already organized: {path_dataset}')
        path_organized = path_dataset
    else:
        path_organized = Path(path_save) if path_save else path_dataset.with_name(path_dataset.name + '_organized')
        if path_organized.exists() and any(path_organized.iterdir()):
            raise ValueError(f'The save folder is not empty: {path_organized}')
        organize(path_organized, dicom_files)

    update_headers(path_organized)
    print(f'DONE, the organized dataset is in: {path_organized}')


if __name__ == "__main__":
    # setting up arguments:
    parser = argparse.ArgumentParser(description='Re-organize dataset to follow MEDiml package conventions.')
    parser.add_argument("--path-dataset", required=True, help="Path to your dataset folder.")
    parser.add_argument("--path-save", required=False, default=None,
                        help="Path where to save the organized dataset (if not organized yet). "
                             "Defaults to '<path-dataset>_organized'.")
    args = parser.parse_args()

    # main
    main(args.path_dataset, args.path_save)
