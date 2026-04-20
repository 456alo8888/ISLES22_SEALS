# Implemented: SOOP Batch Input Staging And Batch Segmentation

## What Was Implemented

I implemented the plan in two practical layers:

1. A CSV-driven staging flow that converts SOOP `.nii.gz` DWI and ADC files into per-subject `.mha` folders using the original `sub-xxxx` identifiers.
2. A batch segmentation path that can consume those staged subject folders and convert them into a multi-case nnU-Net test set, then run the repo’s prediction/recovery/ensemble/export flow in batch.

## Files Added

### Phase 1: Staging And Validation

- [scripts/prepare_soop_batch_input.py](../../../scripts/prepare_soop_batch_input.py)
  - Reads `SOOP_modalities_dataset.csv`
  - Filters rows by `has_trace`, `has_adc`, `trace_path`, and `adc_path`
  - Writes:
    - `input/sub-xxxx/dwi-brain-mri/dwi.mha`
    - `input/sub-xxxx/adc-brain-mri/adc.mha`
  - Supports:
    - `--csv-path`
    - `--output-root`
    - `--subjects`
    - `--overwrite`
    - `--dry-run`
    - `--manifest-path`

- [scripts/validate_soop_batch_input.py](../../../scripts/validate_soop_batch_input.py)
  - Validates staged `dwi.mha` and `adc.mha` files
  - Can compare staged outputs against source `.nii.gz` metadata with `--check-source-metadata`

### Phase 2: Batch Segmentation Support

- [nnunet_launcher_batch.sh](../../../nnunet_launcher_batch.sh)
  - Separate batch launcher
  - Keeps the single-subject `nnunet_launcher.sh` intact

## Files Updated

- [nnunet/isles22_input.py](../../../nnunet/isles22_input.py)
  - Added batch input root resolution
  - Added subject-folder enumeration
  - Added case-id handling
  - Added batch case manifest save/load helpers

- [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)
  - Still supports the original single-subject path
  - Now also supports:
    - `--batch-input-root`
    - `--case-manifest`
    - `--task-name`
  - Writes one `_0000` and `_0001` file per staged subject in batch mode
  - Clears stale `imagesTs/*.nii.gz` before regenerating the test set

- [recover_softmax.py](../../../recover_softmax.py)
  - Added `--case-manifest`
  - Uses per-case DWI/ADC geometry in batch mode
  - Preserves original single-subject behavior when no manifest is provided

- [threshold_redirect.py](../../../threshold_redirect.py)
  - Added `--case-manifest`
  - Exports one final `.mha` per case in batch mode
  - Writes a multi-entry `result.json`
  - Preserves single-subject behavior when no manifest is provided

- [README.md](../../../README.md)
  - Added practical instructions for:
    - Phase 1 staging
    - Phase 2 batch segmentation

- [thoughts/shared/research/plan.md](./plan.md)
  - Updated automated verification checkboxes for the items that were actually run

## Verification That Was Run

The following automated checks were executed successfully:

- `python scripts/prepare_soop_batch_input.py --help`
- `python scripts/validate_soop_batch_input.py --help`
- Staged two real subjects from the CSV into `/tmp/soop_stage_test`
- Validated those staged subjects against the original `.nii.gz` spacing and size
- Ran batch dataset conversion on the staged subset and confirmed `imagesTs` contains:
  - `sub-100_0000.nii.gz`
  - `sub-100_0001.nii.gz`
  - `sub-1001_0000.nii.gz`
  - `sub-1001_0001.nii.gz`
- Ran `threshold_redirect.py` in batch mode on a synthetic two-case prediction folder and confirmed it exported:
  - `sub-100.mha`
  - `sub-1001.mha`
  - a two-entry `result.json`
- Python syntax validation:
  - `python -m py_compile ...`
- Shell syntax validation:
  - `bash -n nnunet_launcher_batch.sh`

## Notes From Verification

- The `.nii.gz` to `.mha` conversion emitted SimpleITK warnings about unsupported metadata fields such as `ITK_FileNotes`, `aux_file`, `descrip`, `intent_name`, and `qto_xyz`. The conversions still completed successfully and the staged `.mha` files were readable.
- I verified the staged subset against source metadata for:
  - `sub-100`
  - `sub-1001`
- I did not run the full batch inference end to end because that depends on the local GPU/model runtime conditions already discussed earlier.

## How To Run Phase 1: Transform And Organize Subjects

Run the staging script on the full CSV:

```bash
python scripts/prepare_soop_batch_input.py \
  --csv-path /mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv \
  --output-root input
```

Run it on a subset:

```bash
python scripts/prepare_soop_batch_input.py \
  --csv-path /mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv \
  --output-root input \
  --subjects sub-100,sub-1001
```

Overwrite existing staged outputs:

```bash
python scripts/prepare_soop_batch_input.py \
  --csv-path /mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv \
  --output-root input \
  --overwrite
```

Dry-run without writing files:

```bash
python scripts/prepare_soop_batch_input.py \
  --csv-path /mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv \
  --output-root input \
  --dry-run
```

Validate staged output:

```bash
python scripts/validate_soop_batch_input.py \
  --csv-path /mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv \
  --input-root input \
  --subjects sub-100,sub-1001 \
  --check-source-metadata
```

Expected folder shape after Phase 1:

```text
input/
  sub-100/
    dwi-brain-mri/dwi.mha
    adc-brain-mri/adc.mha
  sub-1001/
    dwi-brain-mri/dwi.mha
    adc-brain-mri/adc.mha
```

## How To Run Phase 2: Batch Segmentation

After Phase 1 staging is complete, run the batch launcher:

```bash
BATCH_INPUT_ROOT=input \
NNUNET_GPU=0 \
bash nnunet_launcher_batch.sh
```

What the batch launcher does:

1. Reads all staged subject folders under `BATCH_INPUT_ROOT`
2. Builds nnU-Net multi-case `imagesTs` and a case manifest
3. Runs five fold predictions with overwrite enabled
4. Recovers softmax arrays back to each subject’s original geometry
5. Ensembles the five folds
6. Exports one final `.mha` per subject and writes `result.json`

Main output locations for Phase 2:

- Multi-case nnU-Net inputs:
  - `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/`
- Case manifest:
  - `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/case_manifest.json`
- Fold predictions:
  - `test_result/preliminary_phase/fold0` through `fold4`
- Recovered softmax:
  - `test_result_recover/preliminary_phase/fold0` through `fold4`
- Ensemble outputs:
  - `test_ensemble/`
- Final batch masks:
  - `output/batch/images/stroke-lesion-segmentation/`

## Recommended Manual Checks

For Phase 1:

- Inspect a few staged `.mha` files visually
- Confirm folder names match the original `subject_id`
- Confirm `dwi.mha` and `adc.mha` exist for each expected subject

For Phase 2:

- Confirm the number of final exported masks matches the number of staged subjects
- Trace at least two subjects end to end:
  - CSV row
  - staged `input/sub-xxxx/...`
  - `imagesTs/sub-xxxx_000{0,1}.nii.gz`
  - fold outputs
  - ensemble output
  - final exported `.mha`

## Remaining Boundary

The batch segmentation implementation is in place, but full end-to-end runtime still depends on the same environment constraints as the single-subject flow:

- installed model weights
- working torch/CUDA environment
- enough GPU memory for inference

Those environment/runtime constraints were not changed by this implementation.
