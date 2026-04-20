---
date: 2026-04-20T14:56:11+07:00
researcher: Codex
git_commit: eb2fd3f
branch: master
repository: ISLES22_SEALS
topic: "nnunet_launcher.sh path and dataset assumptions"
tags: [research, codebase, nnunet, dataset-paths, isles22]
status: complete
last_updated: 2026-04-20
last_updated_by: Codex
---

# Research: nnunet_launcher.sh path and dataset assumptions

**Date**: 2026-04-20T14:56:11+07:00
**Researcher**: Codex
**Git Commit**: `eb2fd3f`
**Branch**: `master`
**Repository**: `ISLES22_SEALS`

## Research Question
Document the file-path and dataset assumptions in this repo for `nnunet_launcher.sh` and the scripts it calls. Focus on `nnunet_launcher.sh`, `nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py`, `recover_softmax.py`, `threshold_redirect.py`, `ensemble_predictions.py`, and the local `input/` directory. Explain what paths each stage reads/writes and which reported tracebacks follow from missing files.

## Summary
`nnunet_launcher.sh` runs a fixed pipeline of dataset conversion, five `nnUNet_predict` calls, five `recover_softmax.py` calls, an ensemble merge, and a final redirect step ([nnunet_launcher.sh:1](../../../nnunet_launcher.sh), [nnunet_launcher.sh:6](../../../nnunet_launcher.sh), [nnunet_launcher.sh:11](../../../nnunet_launcher.sh), [nnunet_launcher.sh:66](../../../nnunet_launcher.sh), [nnunet_launcher.sh:101](../../../nnunet_launcher.sh), [nnunet_launcher.sh:109](../../../nnunet_launcher.sh)).

The dataset conversion step reads from the absolute path `/input/images`, while `recover_softmax.py` and `threshold_redirect.py` read from the repo-relative path `input/images` ([Task500_Ischemic_Stroke_Test.py:125](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py), [recover_softmax.py:106](../../../recover_softmax.py), [threshold_redirect.py:94](../../../threshold_redirect.py)). In the current workspace, `input/images` exists with `dwi-brain-mri/dwi.mha` and `adc-brain-mri/adc.mha`, but there is no `flair-brain-mri/` directory, and `/input/images` does not exist.

The reported `IndexError` tracebacks come from `glob(...)[0]` lookups in the dataset loader classes when a required directory has no `.mha` matches. The reported `FileNotFoundError` in `ensemble_predictions.py` comes from trying to list `.npz` files in `test_result_recover/preliminary_phase/fold0` before that directory exists. The reported `ImportError` from `torch/lib/libtorch_cpu.so` occurs during `torch` import and is not a missing-input-file traceback.

## Detailed Findings

### Local input tree
Current repo-local input contents:

- `input/images/dwi-brain-mri/dwi.mha`
- `input/images/adc-brain-mri/adc.mha`

Observed absent paths in this workspace:

- `/input`
- `/input/images`
- `input/images/flair-brain-mri/`

These observations match the path lookups in the scripts and determine which `glob(...)[0]` access fails first.

### Stage 1: Dataset conversion
`nnunet_launcher.sh` first exports nnU-Net environment variables and then runs `python nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py` ([nnunet_launcher.sh:1-6](../../../nnunet_launcher.sh)).

Inside `Task500_Ischemic_Stroke_Test.py`, `ISLES22.load_data()` looks for three modality folders under `self.root`:

- `dwi-brain-mri/*.mha`
- `adc-brain-mri/*.mha`
- `flair-brain-mri/*.mha`

The code indexes the first match from each glob directly ([Task500_Ischemic_Stroke_Test.py:29-36](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)). In `__main__`, `raw_data_dir` is hard-coded to `/input/images` ([Task500_Ischemic_Stroke_Test.py:124-127](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)).

If loading succeeds, the script writes nnU-Net test-set artifacts under `join(nnUNet_raw_data, "Task500_Ischemic_Stroke_Test")`, with these subdirectories created up front:

- `imagesTr`
- `labelsTr`
- `imagesTs`
- `labelsTs`

([Task500_Ischemic_Stroke_Test.py:129-139](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py))

It then writes:

- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/ISLES22_0001_0000.nii.gz`
- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/ISLES22_0001_0001.nii.gz`
- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/dataset.json`

([Task500_Ischemic_Stroke_Test.py:145-156](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py))

### Stage 2: nnU-Net prediction
The launcher runs `nnUNet_change_trainer_class` against the trained-model directory:

- `data/nnUNet_trained_models/nnUNet/3d_fullres/Task012_Ischemic_Stroke_TM_Fullset/nnUNetTrainerV2_DDP__nnUNetPlansv2.1`

([nnunet_launcher.sh:8-9](../../../nnunet_launcher.sh))

Then it runs five `nnUNet_predict` commands with the same input directory:

- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/`

and these fold-specific output directories:

- `test_result/preliminary_phase/fold0`
- `test_result/preliminary_phase/fold1`
- `test_result/preliminary_phase/fold2`
- `test_result/preliminary_phase/fold3`
- `test_result/preliminary_phase/fold4`

([nnunet_launcher.sh:11-64](../../../nnunet_launcher.sh))

The model root exists in the current workspace, including `fold_0` through `fold_4` and `plans.pkl` under the trainer directory.

### Stage 3: Softmax recovery
The launcher invokes `recover_softmax.py` five times, each time with:

- `-i test_result`
- `-m preliminary_phase`
- `-f foldN`
- `-o test_result_recover/preliminary_phase/foldN`

([nnunet_launcher.sh:66-94](../../../nnunet_launcher.sh))

Within `recover_softmax.py`, `raw_data_dir` is `input/images` (repo-relative), not `/input/images` ([recover_softmax.py:106-108](../../../recover_softmax.py)). Its `ISLES22.load_data()` performs the same three `glob(...)[0]` lookups for DWI, ADC, and FLAIR as the dataset-conversion script ([recover_softmax.py:28-35](../../../recover_softmax.py)).

If loading succeeds, the script creates `output_folder` if missing ([recover_softmax.py:110-111](../../../recover_softmax.py)), then reads all `.npz` files from:

- `os.path.join(input_folder, model_type, fold_index, '*.npz')`

which resolves here to `test_result/preliminary_phase/foldN/*.npz` ([recover_softmax.py:113](../../../recover_softmax.py)).

For each `.npz`, it also reads the sibling `.pkl` file by replacing the suffix `npz` with `pkl` ([recover_softmax.py:115-120](../../../recover_softmax.py)). Each recovered softmax is written back as:

- `test_result_recover/preliminary_phase/foldN/<same-basename>.npz`

([recover_softmax.py:137-139](../../../recover_softmax.py))

### Stage 4: Ensemble merge
The launcher sets five recovered-fold directories as shell variables and passes them to `python -m ensemble_predictions` with output `test_ensemble/` and `--npz` ([nnunet_launcher.sh:96-107](../../../nnunet_launcher.sh)).

`ensemble_predictions.py` creates the output folder with `maybe_mkdir_p(output_folder)` ([ensemble_predictions.py:110-111](../../../ensemble_predictions.py)). It then reads `.npz` basenames from every folder argument using:

- `subfiles(i, suffix=".npz", join=False)`

([ensemble_predictions.py:120-123](../../../ensemble_predictions.py))

It requires every fold folder to contain the same patient `.npz` files ([ensemble_predictions.py:125-127](../../../ensemble_predictions.py)). For each patient id, it writes:

- `test_ensemble/<patient>.mha`

and, because `--npz` is passed, also:

- `test_ensemble/<patient>.npz`

([ensemble_predictions.py:131-137](../../../ensemble_predictions.py), [ensemble_predictions.py:104-107](../../../ensemble_predictions.py))

### Stage 5: Threshold redirect
The final launcher step runs:

- `python threshold_redirect.py -i test_ensemble/ -o output/images/stroke-lesion-segmentation/`

([nnunet_launcher.sh:109-111](../../../nnunet_launcher.sh))

`threshold_redirect.py` also uses repo-relative `input/images` as its dataset root ([threshold_redirect.py:93-96](../../../threshold_redirect.py)). Its loader again expects:

- `input/images/dwi-brain-mri/*.mha`
- `input/images/adc-brain-mri/*.mha`
- `input/images/flair-brain-mri/*.mha`

([threshold_redirect.py:22-29](../../../threshold_redirect.py))

If dataset loading succeeds, the script reads the first `.mha` prediction from `input_folder`:

- `glob(os.path.join(input_folder, '*.mha'))[0]`

([threshold_redirect.py:101-104](../../../threshold_redirect.py))

If that lookup fails, the script catches the exception and instead creates a zero mask based on the DWI image shape ([threshold_redirect.py:101-109](../../../threshold_redirect.py)). It then writes:

- `output/images/stroke-lesion-segmentation/<dwi filename>`
- `output/images/stroke-lesion-segmentation/result.json`

([threshold_redirect.py:115-128](../../../threshold_redirect.py))

## Traceback Mapping

### `Task500_Ischemic_Stroke_Test.py` `IndexError`
Reported traceback:

- `self.dwi_path = glob(os.path.join(self.root, dwi_folder, '*.mha'))[0]`

([Task500_Ischemic_Stroke_Test.py:34](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py))

This follows from the dataset conversion script using `raw_data_dir = '/input/images'` ([Task500_Ischemic_Stroke_Test.py:125](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)). In the current workspace, `/input/images` does not exist, so the DWI glob under `/input/images/dwi-brain-mri/*.mha` returns an empty list and indexing `[0]` raises the reported `IndexError`.

### `recover_softmax.py` `IndexError`
Reported traceback:

- `self.flair_path = glob(os.path.join(self.root, flair_folder, '*.mha'))[0]`

([recover_softmax.py:35](../../../recover_softmax.py))

This follows from `recover_softmax.py` using `raw_data_dir = 'input/images'` ([recover_softmax.py:106](../../../recover_softmax.py)). In the current workspace, `input/images/dwi-brain-mri/dwi.mha` and `input/images/adc-brain-mri/adc.mha` exist, so those two glob lookups can resolve first. There is no `input/images/flair-brain-mri/`, so the FLAIR glob returns an empty list and indexing `[0]` raises the reported `IndexError`.

### `threshold_redirect.py` `IndexError`
Reported traceback:

- `self.flair_path = glob(os.path.join(self.root, flair_folder, '*.mha'))[0]`

([threshold_redirect.py:29](../../../threshold_redirect.py))

This follows from the same repo-relative dataset assumption as `recover_softmax.py` ([threshold_redirect.py:94](../../../threshold_redirect.py)). The script reaches dataset loading before its `try/except` around `glob(os.path.join(input_folder, '*.mha'))[0]` ([threshold_redirect.py:101-109](../../../threshold_redirect.py)), so the missing local FLAIR path causes the reported `IndexError` before the script can fall back to a zero mask.

### `ensemble_predictions.py` `FileNotFoundError`
Reported traceback:

- `FileNotFoundError: [Errno 2] No such file or directory: 'test_result_recover/preliminary_phase/fold0'`

([ensemble_predictions.py:120](../../../ensemble_predictions.py))

This follows from `merge()` calling `subfiles(i, suffix=".npz", join=False)` on every folder passed from the launcher ([ensemble_predictions.py:120](../../../ensemble_predictions.py), [nnunet_launcher.sh:96-107](../../../nnunet_launcher.sh)). When `test_result_recover/preliminary_phase/fold0` does not exist, `os.listdir(folder)` inside `subfiles` raises the reported `FileNotFoundError`. The current workspace contains `test_ensemble/` and `output/images/stroke-lesion-segmentation/`, but not `test_result/` or `test_result_recover/`.

### `nnUNet_predict` `ImportError`
Reported traceback:

- `ImportError: .../torch/lib/libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`

This traceback occurs while importing `torch` from `nnunet/inference/predict_simple.py` before prediction I/O is performed. It is not a missing-input-file or missing-directory traceback from the dataset paths documented above.

## Code References
- `nnunet_launcher.sh:1-111` - Full launcher pipeline and all read/write path arguments.
- `nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:29-36` - Dataset loader glob assumptions for DWI, ADC, and FLAIR.
- `nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:124-156` - Absolute dataset root `/input/images` and nnU-Net raw-data outputs.
- `recover_softmax.py:28-35` - Repo-relative dataset loader glob assumptions.
- `recover_softmax.py:106-139` - Reads from `test_result/preliminary_phase/foldN/*.npz` and writes recovered `.npz` files.
- `threshold_redirect.py:22-29` - Repo-relative dataset loader glob assumptions.
- `threshold_redirect.py:93-128` - Reads `test_ensemble/*.mha`, writes final `.mha` and `result.json`.
- `ensemble_predictions.py:110-137` - Reads recovered fold folders, enumerates `.npz`, and writes ensemble outputs.

## Architecture Documentation
The launcher is organized as a linear filesystem pipeline:

1. Source modalities are loaded from an input dataset root.
2. The dataset-conversion step writes nnU-Net test inputs under `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/`.
3. `nnUNet_predict` writes fold-specific outputs under `test_result/preliminary_phase/foldN/`.
4. `recover_softmax.py` rewrites those fold outputs into `test_result_recover/preliminary_phase/foldN/`.
5. `ensemble_predictions.py` merges recovered fold `.npz` files into `test_ensemble/`.
6. `threshold_redirect.py` converts `test_ensemble/` output into the final `output/images/stroke-lesion-segmentation/` payload.

The dataset loader logic is duplicated across three scripts, but with two different root-path conventions: one absolute (`/input/images`) and two repo-relative (`input/images`).

## Historical Context (from thoughts/)
No pre-existing `thoughts/` material was present in this workspace before this research note.

## Related Research
None found in this workspace.

## Open Questions
- No additional questions were investigated beyond the requested path and traceback mapping.
