import argparse
import json
import os
from glob import glob

import numpy as np
import SimpleITK as sitk

from nnunet.isles22_input import load_case_manifest, load_case_paths, resolve_input_root


def json_writer(json_path, data):
    with open(str(json_path), "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def case_output_filename(case_id, manifest_case):
    if manifest_case:
        return f"{manifest_case['subject_id']}.mha"
    return "dwi.mha"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input_folder", required=True)
    parser.add_argument("-o", "--output_folder", required=True)
    parser.add_argument("--case-manifest", default=None)
    args = parser.parse_args()

    os.makedirs(args.output_folder, exist_ok=True)
    manifest_map = load_case_manifest(args.case_manifest) if args.case_manifest else None
    predictions = sorted(glob(os.path.join(args.input_folder, "*.mha")))

    if not predictions:
        if manifest_map:
            case_ids = sorted(manifest_map.keys())
        else:
            case_ids = ["ISLES22_0001"]
    else:
        case_ids = [os.path.splitext(os.path.basename(path))[0] for path in predictions]

    case_results = []
    single_case_paths = None if manifest_map else load_case_paths(resolve_input_root())

    for case_id in case_ids:
        manifest_case = manifest_map.get(case_id) if manifest_map else None
        if manifest_case:
            dwi_path = manifest_case["dwi_path"]
        else:
            dwi_path = single_case_paths["dwi_path"]

        image_file = sitk.ReadImage(dwi_path)
        pred_path = os.path.join(args.input_folder, f"{case_id}.mha")
        if os.path.exists(pred_path):
            pred_image = sitk.ReadImage(pred_path)
        else:
            image_array = sitk.GetArrayFromImage(image_file)
            pred_array = np.zeros_like(image_array)
            pred_image = sitk.GetImageFromArray(pred_array)

        pred_image.SetOrigin(image_file.GetOrigin())
        pred_image.SetSpacing(image_file.GetSpacing())
        pred_image.SetDirection(image_file.GetDirection())

        output_filename = case_output_filename(case_id, manifest_case)
        sitk.WriteImage(pred_image, os.path.join(args.output_folder, output_filename))
        case_results.append(
            {
                "outputs": [
                    {
                        "type": "Image",
                        "slug": "stroke-lesion-segmentation",
                        "filename": output_filename,
                    }
                ],
                "inputs": [
                    {
                        "type": "Image",
                        "slug": "dwi-brain-mri",
                        "filename": output_filename,
                    }
                ],
            }
        )

    json_writer(os.path.join(args.output_folder, "result.json"), case_results)


if __name__ == "__main__":
    main()
