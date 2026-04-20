import argparse
import csv
import json
from pathlib import Path

import SimpleITK as sitk


def normalize_column_name(name):
    return str(name).strip().lstrip("\ufeff[").rstrip("]")


DEFAULT_CSV = "/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv"


def str_to_bool(value):
    return str(value).strip() in {"1", "true", "True", "yes"}


def parse_subject_subset(raw_value):
    if not raw_value:
        return None
    return {item.strip() for item in raw_value.split(",") if item.strip()}


def main():
    parser = argparse.ArgumentParser(description="Validate staged SOOP batch input folders.")
    parser.add_argument("--csv-path", default=DEFAULT_CSV)
    parser.add_argument("--input-root", default="input")
    parser.add_argument("--subjects", default=None)
    parser.add_argument("--check-source-metadata", action="store_true")
    args = parser.parse_args()

    subset = parse_subject_subset(args.subjects)
    input_root = Path(args.input_root)
    summary = {"validated": [], "missing": [], "failed": []}

    with open(args.csv_path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            reader.fieldnames = [normalize_column_name(name) for name in reader.fieldnames]
        for row in reader:
            row = {normalize_column_name(key): value for key, value in row.items()}
            subject_id = row["subject_id"].strip()
            if subset and subject_id not in subset:
                continue
            if not (str_to_bool(row.get("has_trace")) and str_to_bool(row.get("has_adc"))):
                continue

            dwi_path = input_root / subject_id / "dwi-brain-mri" / "dwi.mha"
            adc_path = input_root / subject_id / "adc-brain-mri" / "adc.mha"
            if not dwi_path.exists() or not adc_path.exists():
                summary["missing"].append(
                    {
                        "subject_id": subject_id,
                        "dwi_path": str(dwi_path),
                        "adc_path": str(adc_path),
                    }
                )
                continue

            try:
                dwi_image = sitk.ReadImage(str(dwi_path))
                adc_image = sitk.ReadImage(str(adc_path))
                record = {
                    "subject_id": subject_id,
                    "dwi_path": str(dwi_path),
                    "adc_path": str(adc_path),
                    "dwi_size": list(dwi_image.GetSize()),
                    "adc_size": list(adc_image.GetSize()),
                }

                if args.check_source_metadata:
                    source_dwi = sitk.ReadImage(row["trace_path"])
                    source_adc = sitk.ReadImage(row["adc_path"])
                    record["dwi_spacing_matches"] = list(source_dwi.GetSpacing()) == list(dwi_image.GetSpacing())
                    record["adc_spacing_matches"] = list(source_adc.GetSpacing()) == list(adc_image.GetSpacing())
                    record["dwi_size_matches"] = list(source_dwi.GetSize()) == list(dwi_image.GetSize())
                    record["adc_size_matches"] = list(source_adc.GetSize()) == list(adc_image.GetSize())

                summary["validated"].append(record)
            except Exception as exc:
                summary["failed"].append({"subject_id": subject_id, "reason": str(exc)})

    print(json.dumps(summary, indent=2))
    if summary["missing"] or summary["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
