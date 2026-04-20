import argparse
import csv
import json
import os
from pathlib import Path

import SimpleITK as sitk


DEFAULT_CSV = "/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv"


def normalize_column_name(name):
    return str(name).strip().lstrip("\ufeff[").rstrip("]")


def str_to_bool(value):
    return str(value).strip() in {"1", "true", "True", "yes"}


def convert_image(input_path, output_path):
    image = sitk.ReadImage(str(input_path))
    sitk.WriteImage(image, str(output_path))


def parse_subject_subset(raw_value):
    if not raw_value:
        return None
    return {item.strip() for item in raw_value.split(",") if item.strip()}


def subject_output_paths(output_root, subject_id):
    subject_root = Path(output_root) / subject_id
    return {
        "subject_root": subject_root,
        "dwi_dir": subject_root / "dwi-brain-mri",
        "adc_dir": subject_root / "adc-brain-mri",
        "dwi_path": subject_root / "dwi-brain-mri" / "dwi.mha",
        "adc_path": subject_root / "adc-brain-mri" / "adc.mha",
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Prepare staged SOOP batch input as per-subject .mha folders.")
    parser.add_argument("--csv-path", default=DEFAULT_CSV)
    parser.add_argument("--output-root", default="input")
    parser.add_argument("--subjects", default=None, help="Comma-separated subject_id subset")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--manifest-path",
        default=None,
        help="Optional explicit manifest path. Defaults to <output-root>/soop_batch_manifest.json",
    )
    return parser


def main():
    args = build_parser().parse_args()
    subset = parse_subject_subset(args.subjects)
    output_root = Path(args.output_root)
    manifest_path = Path(args.manifest_path) if args.manifest_path else output_root / "soop_batch_manifest.json"

    summary = {
        "csv_path": str(Path(args.csv_path).resolve()),
        "output_root": str(output_root.resolve()),
        "converted": [],
        "skipped": [],
        "failed": [],
        "total_rows": 0,
        "eligible_rows": 0,
    }

    with open(args.csv_path, "r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames:
            reader.fieldnames = [normalize_column_name(name) for name in reader.fieldnames]
        for row in reader:
            summary["total_rows"] += 1
            normalized_row = {normalize_column_name(key): value for key, value in row.items()}
            subject_id = normalized_row["subject_id"].strip()
            if subset and subject_id not in subset:
                continue

            has_trace = str_to_bool(normalized_row.get("has_trace"))
            has_adc = str_to_bool(normalized_row.get("has_adc"))
            trace_path = Path(normalized_row["trace_path"])
            adc_path = Path(normalized_row["adc_path"])

            if not (has_trace and has_adc):
                summary["skipped"].append(
                    {"subject_id": subject_id, "reason": "missing modality flags"}
                )
                continue

            if not (trace_path.exists() and adc_path.exists()):
                summary["failed"].append(
                    {
                        "subject_id": subject_id,
                        "reason": "source path missing",
                        "trace_path": str(trace_path),
                        "adc_path": str(adc_path),
                    }
                )
                continue

            summary["eligible_rows"] += 1
            output_paths = subject_output_paths(output_root, subject_id)
            if (
                output_paths["dwi_path"].exists()
                and output_paths["adc_path"].exists()
                and not args.overwrite
            ):
                summary["skipped"].append(
                    {"subject_id": subject_id, "reason": "outputs already exist"}
                )
                continue

            if args.dry_run:
                summary["converted"].append(
                    {
                        "subject_id": subject_id,
                        "trace_path": str(trace_path),
                        "adc_path": str(adc_path),
                        "dwi_output": str(output_paths["dwi_path"]),
                        "adc_output": str(output_paths["adc_path"]),
                        "dry_run": True,
                    }
                )
                continue

            output_paths["dwi_dir"].mkdir(parents=True, exist_ok=True)
            output_paths["adc_dir"].mkdir(parents=True, exist_ok=True)

            try:
                convert_image(trace_path, output_paths["dwi_path"])
                convert_image(adc_path, output_paths["adc_path"])
            except Exception as exc:
                summary["failed"].append({"subject_id": subject_id, "reason": str(exc)})
                continue

            summary["converted"].append(
                {
                    "subject_id": subject_id,
                    "trace_path": str(trace_path),
                    "adc_path": str(adc_path),
                    "dwi_output": str(output_paths["dwi_path"]),
                    "adc_output": str(output_paths["adc_path"]),
                }
            )

    output_root.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(
        {
            "csv_path": summary["csv_path"],
            "output_root": summary["output_root"],
            "total_rows": summary["total_rows"],
            "eligible_rows": summary["eligible_rows"],
            "converted": len(summary["converted"]),
            "skipped": len(summary["skipped"]),
            "failed": len(summary["failed"]),
            "manifest_path": str(manifest_path),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
