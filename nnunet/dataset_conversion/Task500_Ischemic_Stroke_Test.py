#    Copyright 2020 Division of Medical Image Computing, German Cancer Research Center (DKFZ), Heidelberg, Germany
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
import argparse
import os

import numpy as np
import SimpleITK as sitk

from batchgenerators.utilities.file_and_folder_operations import join, maybe_mkdir_p
from nnunet.dataset_conversion.utils import generate_dataset_json
from nnunet.isles22_input import (
    enumerate_batch_cases,
    load_case_paths,
    resolve_batch_input_root,
    resolve_input_root,
    save_case_manifest,
)
from nnunet.paths import nnUNet_raw_data


def respacing_file(image_file, target_spacing, resample_method):
    if type(image_file) is not sitk.SimpleITK.Image:
        image_file = sitk.ReadImage(image_file)
    if not isinstance(target_spacing, np.ndarray):
        target_spacing = np.array(target_spacing)

    resampler_image = sitk.ResampleImageFilter()
    origin_spacing = np.array(image_file.GetSpacing())
    origin_size = np.array(image_file.GetSize())
    factor = np.array(target_spacing / origin_spacing)
    target_size = np.maximum(np.round(origin_size / factor).astype(np.int64), 1)

    resampler_image.SetReferenceImage(image_file)
    resampler_image.SetOutputSpacing(target_spacing.tolist())
    resampler_image.SetSize(target_size.tolist())
    resampler_image.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler_image.SetInterpolator(resample_method)
    return resampler_image.Execute(image_file)


def reimplement_resize(image_file, target_file, resample_method=sitk.sitkLinear):
    if isinstance(image_file, str):
        image_file = sitk.ReadImage(image_file)
    elif type(image_file) is not sitk.SimpleITK.Image:
        raise AssertionError("Unknown data type to respaceing!")

    if isinstance(target_file, str):
        target_file = sitk.ReadImage(target_file)
    elif type(target_file) is not sitk.SimpleITK.Image:
        raise AssertionError("Unknown data type to respaceing!")

    resampler_image = sitk.ResampleImageFilter()
    resampler_image.SetReferenceImage(image_file)
    resampler_image.SetOutputOrigin(target_file.GetOrigin())
    resampler_image.SetOutputDirection(target_file.GetDirection())
    resampler_image.SetOutputSpacing(target_file.GetSpacing())
    resampler_image.SetSize(target_file.GetSize())
    if resample_method == sitk.sitkNearestNeighbor:
        resampler_image.SetOutputPixelType(sitk.sitkUInt8)
    else:
        resampler_image.SetOutputPixelType(sitk.sitkFloat32)
    resampler_image.SetTransform(sitk.Transform(3, sitk.sitkIdentity))
    resampler_image.SetInterpolator(resample_method)
    return resampler_image.Execute(image_file)


def convert_case(case, target_images_ts):
    dwi_file = respacing_file(
        case["dwi_path"], target_spacing=[1, 1, 1], resample_method=sitk.sitkLinear
    )
    adc_file = reimplement_resize(
        case["adc_path"], target_file=dwi_file, resample_method=sitk.sitkLinear
    )

    sitk.WriteImage(dwi_file, join(target_images_ts, f'{case["case_id"]}_0000.nii.gz'))
    sitk.WriteImage(adc_file, join(target_images_ts, f'{case["case_id"]}_0001.nii.gz'))


def single_case_from_root(raw_data_dir):
    paths = load_case_paths(raw_data_dir)
    return [
        {
            "subject_id": "ISLES22_0001",
            "case_id": "ISLES22_0001",
            "root": raw_data_dir,
            **paths,
        }
    ]


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-name", default="Task500_Ischemic_Stroke_Test")
    parser.add_argument("--batch-input-root", default=None)
    parser.add_argument("--case-manifest", default=None)
    return parser


def main():
    args = build_parser().parse_args()

    if args.batch_input_root:
        batch_root = resolve_batch_input_root(args.batch_input_root)
        cases = enumerate_batch_cases(batch_root)
        if not cases:
            raise FileNotFoundError(
                f"No staged subject folders with DWI/ADC modalities found under {batch_root}"
            )
    else:
        raw_data_dir = resolve_input_root()
        cases = single_case_from_root(raw_data_dir)

    target_base = join(nnUNet_raw_data, args.task_name)
    target_images_tr = join(target_base, "imagesTr")
    target_labels_tr = join(target_base, "labelsTr")
    target_images_ts = join(target_base, "imagesTs")
    target_labels_ts = join(target_base, "labelsTs")

    maybe_mkdir_p(target_base)
    maybe_mkdir_p(target_images_tr)
    maybe_mkdir_p(target_labels_tr)
    maybe_mkdir_p(target_images_ts)
    maybe_mkdir_p(target_labels_ts)

    for entry in os.listdir(target_images_ts):
        if entry.endswith(".nii.gz"):
            os.remove(join(target_images_ts, entry))

    for case in cases:
        convert_case(case, target_images_ts)

    generate_dataset_json(
        output_file=join(target_base, "dataset.json"),
        imagesTr_dir=target_images_tr,
        imagesTs_dir=target_images_ts,
        modalities=("dwi", "adc"),
        labels={0: "background", 1: "Ischemic Stroke"},
        dataset_name=args.task_name,
        sort_keys=True,
        license="ISLES22 license",
    )

    if args.case_manifest:
        maybe_mkdir_p(os.path.dirname(args.case_manifest))
        save_case_manifest(args.case_manifest, cases)


if __name__ == "__main__":
    main()
