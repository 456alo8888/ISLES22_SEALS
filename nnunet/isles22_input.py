import json
import os
import re
from glob import glob


DWI_FOLDER = "dwi-brain-mri"
ADC_FOLDER = "adc-brain-mri"
FLAIR_FOLDER = "flair-brain-mri"


def resolve_input_root():
    candidates = ("/input/images", "input/images")
    for root in candidates:
        if os.path.isdir(root):
            return root
    raise FileNotFoundError(
        "Could not find ISLES22 input folder. Expected one of: /input/images, input/images"
    )


def resolve_batch_input_root(batch_root=None):
    if batch_root:
        if os.path.isdir(batch_root):
            return batch_root
        raise FileNotFoundError(f"Explicit batch input root does not exist: {batch_root}")

    candidates = ["/input", "input"]

    for root in candidates:
        if not os.path.isdir(root):
            continue
        return root

    raise FileNotFoundError(
        "Could not find batch input root. Expected one of: /input, input, or an explicit batch root"
    )


def require_single_image(root, folder):
    matches = glob(os.path.join(root, folder, "*.mha"))
    if not matches:
        raise FileNotFoundError(
            f"Missing required input image under {os.path.join(root, folder)}"
        )
    return matches[0]


def optional_single_image(root, folder):
    matches = glob(os.path.join(root, folder, "*.mha"))
    return matches[0] if matches else None


def load_case_paths(case_root):
    return {
        "dwi_path": require_single_image(case_root, DWI_FOLDER),
        "adc_path": require_single_image(case_root, ADC_FOLDER),
        "flair_path": optional_single_image(case_root, FLAIR_FOLDER),
    }


def case_id_from_subject(subject_id):
    normalized = re.sub(r"[^A-Za-z0-9_-]+", "_", subject_id.strip())
    if not normalized:
        raise ValueError(f"Cannot derive case id from empty subject id: {subject_id!r}")
    return normalized


def enumerate_batch_cases(batch_root):
    cases = []
    for entry in sorted(os.listdir(batch_root)):
        case_root = os.path.join(batch_root, entry)
        if not os.path.isdir(case_root):
            continue
        dwi_dir = os.path.join(case_root, DWI_FOLDER)
        adc_dir = os.path.join(case_root, ADC_FOLDER)
        if not (os.path.isdir(dwi_dir) and os.path.isdir(adc_dir)):
            continue

        case_paths = load_case_paths(case_root)
        case_id = case_id_from_subject(entry)
        cases.append(
            {
                "subject_id": entry,
                "case_id": case_id,
                "root": case_root,
                **case_paths,
            }
        )
    return cases


def save_case_manifest(manifest_path, cases):
    manifest = {
        "cases": [
            {
                "subject_id": case["subject_id"],
                "case_id": case["case_id"],
                "root": case["root"],
                "dwi_path": case["dwi_path"],
                "adc_path": case["adc_path"],
                "flair_path": case.get("flair_path"),
            }
            for case in cases
        ]
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)


def load_case_manifest(manifest_path):
    with open(manifest_path, "r", encoding="utf-8") as handle:
        manifest = json.load(handle)

    cases = {}
    for case in manifest.get("cases", []):
        cases[case["case_id"]] = case
    return cases
