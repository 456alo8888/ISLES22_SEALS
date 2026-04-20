import argparse
import os
import pickle
from glob import glob

import numpy as np
import SimpleITK as sitk
from tqdm import tqdm

from nnunet.isles22_input import load_case_manifest, load_case_paths, resolve_input_root


def reimplement_resize(image_file, target_file, resample_method=sitk.sitkLinear):
    if isinstance(image_file, str):
        image_file = sitk.ReadImage(image_file)
    elif isinstance(image_file, np.ndarray):
        image_file = sitk.GetImageFromArray(image_file)
    elif type(image_file) is not sitk.SimpleITK.Image:
        raise AssertionError("Unknown data type to respaceing!")

    if isinstance(target_file, str):
        target_file = sitk.ReadImage(target_file)
    elif isinstance(target_file, np.ndarray):
        target_file = sitk.GetImageFromArray(target_file)
    elif type(target_file) is not sitk.SimpleITK.Image:
        raise AssertionError("Unknown data type to respaceing!")

    resampler_image = sitk.ResampleImageFilter()
    resampler_image.SetReferenceImage(image_file)
    resampler_image.SetOutputOrigin(image_file.GetOrigin())
    resampler_image.SetOutputDirection(image_file.GetDirection())
    resampler_image.SetOutputSpacing(target_file.GetSpacing())
    resampler_image.SetSize(target_file.GetSize())
    if resample_method == sitk.sitkNearestNeighbor:
        resampler_image.SetOutputPixelType(sitk.sitkUInt8)
    else:
        resampler_image.SetOutputPixelType(sitk.sitkFloat32)
    resampler_image.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler_image.SetInterpolator(resample_method)
    resampled_image_file = resampler_image.Execute(image_file)
    return sitk.GetArrayFromImage(resampled_image_file)


def load_pkl(pkl_path):
    with open(pkl_path, "rb") as handle:
        return pickle.load(handle)


def get_case_paths(case_id, manifest_map=None, single_case_root=None):
    if manifest_map:
        case = manifest_map[case_id]
        return case["dwi_path"], case["adc_path"]

    case_paths = load_case_paths(single_case_root or resolve_input_root())
    return case_paths["dwi_path"], case_paths["adc_path"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_folder", required=True, help="root_path of 5 folds")
    parser.add_argument("-o", "--output_folder", required=True)
    parser.add_argument("-m", "--model_type", required=True)
    parser.add_argument("-f", "--fold_index", required=True)
    parser.add_argument("--case-manifest", default=None)
    args = parser.parse_args()

    manifest_map = load_case_manifest(args.case_manifest) if args.case_manifest else None
    single_case_root = None if manifest_map else resolve_input_root()

    os.makedirs(args.output_folder, exist_ok=True)
    files_npzs = sorted(glob(os.path.join(args.input_folder, args.model_type, args.fold_index, "*.npz")))

    for file_npz in tqdm(files_npzs):
        case_id = os.path.splitext(os.path.basename(file_npz))[0]
        file_pkl = file_npz.replace("npz", "pkl")
        predict_softmax = np.load(file_npz)["softmax"]
        pkl_dict = load_pkl(file_pkl)
        origin_size = pkl_dict["original_size_of_raw_data"]
        origin_bbox = pkl_dict["crop_bbox"]
        origin_array = np.zeros((2, origin_size[0], origin_size[1], origin_size[2]), dtype=np.float32)
        origin_array[0] = 1.0
        origin_array[
            :,
            origin_bbox[0][0]:origin_bbox[0][1],
            origin_bbox[1][0]:origin_bbox[1][1],
            origin_bbox[2][0]:origin_bbox[2][1],
        ] = predict_softmax.astype(np.float32)

        dwi_path, adc_path = get_case_paths(case_id, manifest_map, single_case_root)
        target_array_shape = sitk.GetArrayFromImage(sitk.ReadImage(dwi_path)).shape
        target_array = np.zeros((2, target_array_shape[0], target_array_shape[1], target_array_shape[2]), dtype=np.float32)
        target_array[0] = reimplement_resize(origin_array[0], dwi_path)
        target_array[1] = reimplement_resize(origin_array[1], adc_path)

        target_file = os.path.join(args.output_folder, f"{case_id}.npz")
        np.savez(target_file, softmax=target_array)


if __name__ == "__main__":
    main()
