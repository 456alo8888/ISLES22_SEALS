---
date: 2026-04-20T17:09:21+07:00
researcher: Codex
git_commit: 6674ce6ebb7891b8a8ff56a1998dba72b4c980b5
branch: master
repository: ISLES22_SEALS
topic: "nnunet_launcher.sh workflow and why changing input did not change the final mask"
tags: [research, codebase, nnunet, workflow, inference, caching]
status: complete
last_updated: 2026-04-20
last_updated_by: Codex
---

# Research: nnunet_launcher.sh workflow and why changing input did not change the final mask

**Date**: 2026-04-20T17:09:21+07:00
**Researcher**: Codex
**Git Commit**: `6674ce6ebb7891b8a8ff56a1998dba72b4c980b5`
**Branch**: `master`
**Repository**: `ISLES22_SEALS`

## Research Question
Read [nnunet_launcher.sh](../../../nnunet_launcher.sh) and document the workflow from reading input to extracting the final mask. Explain why changing files under `input/` can still leave the final mask unchanged.

## Summary
`nnunet_launcher.sh` runs a fixed single-case pipeline:

1. Read DWI and ADC from `input/images`
2. Convert them into nnU-Net test inputs under `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs`
3. Run five fold predictions into `test_result/preliminary_phase/fold0` through `fold4`
4. Recover fold softmax arrays back to the original image geometry under `test_result_recover/preliminary_phase/fold0` through `fold4`
5. Ensemble the five recovered folds into `test_ensemble/`
6. Copy the first ensemble `.mha` into `output/images/stroke-lesion-segmentation/dwi.mha` and write `result.json`

The final mask can stay unchanged after `input/` changes because the launcher does not pass `--overwrite_existing` to `nnUNet_predict` ([nnunet_launcher.sh:23](../../../nnunet_launcher.sh), [predict_simple.py:102](../../../nnunet/inference/predict_simple.py), [predict.py:169](../../../nnunet/inference/predict.py)). Existing fold outputs in `test_result/preliminary_phase/fold*` are therefore reused. In the current workspace, the converted input files in `imagesTs/` are newer than the fold predictions, while the final ensemble and exported mask were rewritten later from those older fold predictions.

## Detailed Findings

### Stage 1: Launcher setup
At startup, the launcher enables shell fail-fast mode, prepares the JIT-profiling shim, exports nnU-Net path variables, and picks a GPU id from `NNUNET_GPU` or `CUDA_VISIBLE_DEVICES` ([nnunet_launcher.sh:1-16](../../../nnunet_launcher.sh)).

The pipeline then runs these stages in order:

- dataset conversion ([nnunet_launcher.sh:18](../../../nnunet_launcher.sh))
- trainer-class rewrite ([nnunet_launcher.sh:20-21](../../../nnunet_launcher.sh))
- five `nnUNet_predict` calls, one per fold ([nnunet_launcher.sh:23-76](../../../nnunet_launcher.sh))
- five `recover_softmax.py` calls ([nnunet_launcher.sh:78-106](../../../nnunet_launcher.sh))
- ensemble merge ([nnunet_launcher.sh:108-119](../../../nnunet_launcher.sh))
- final mask export ([nnunet_launcher.sh:121-123](../../../nnunet_launcher.sh))

### Stage 2: Reading raw input
`Task500_Ischemic_Stroke_Test.py` resolves the input root and loads:

- `dwi-brain-mri/*.mha`
- `adc-brain-mri/*.mha`
- optional `flair-brain-mri/*.mha`

([Task500_Ischemic_Stroke_Test.py:30-37](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py), [Task500_Ischemic_Stroke_Test.py:126-128](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py))

The current input loader requires DWI and ADC and stores the resolved source paths in `dataset_ISLES22.dwi_path` and `dataset_ISLES22.adc_path`.

### Stage 3: Converting input to nnU-Net test files
The conversion step creates the nnU-Net task directory and writes the current input into a fixed single-case test set:

- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/ISLES22_0001_0000.nii.gz`
- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/ISLES22_0001_0001.nii.gz`
- `data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/dataset.json`

([Task500_Ischemic_Stroke_Test.py:130-157](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py))

This script always uses the hard-coded case id `ISLES22_0001` ([Task500_Ischemic_Stroke_Test.py:146-147](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)).

### Stage 4: Fold prediction
Each `nnUNet_predict` call reads from the same `imagesTs/` directory and writes one fold into one fixed output directory under `test_result/preliminary_phase/` ([nnunet_launcher.sh:23-76](../../../nnunet_launcher.sh)).

`predict_simple.py` defines `--overwrite_existing` as a flag that defaults to `False` ([predict_simple.py:102-103](../../../nnunet/inference/predict_simple.py)). The launcher does not pass that flag, so `overwrite_existing` stays `False`.

`predict.py` then filters out already-finished cases when `overwrite_existing` is false:

- it normalizes target filenames to `.nii.gz`
- checks whether the output `.nii.gz` already exists
- if `-z` is used, also checks whether the output `.npz` already exists
- keeps only missing cases in `not_done_idx`

([predict.py:159-179](../../../nnunet/inference/predict.py))

That means an existing pair like:

- `test_result/preliminary_phase/fold0/ISLES22_0001.nii.gz`
- `test_result/preliminary_phase/fold0/ISLES22_0001.npz`

is treated as completed output and is not regenerated.

### Stage 5: Recovering softmax to original geometry
Each `recover_softmax.py` call reads all `.npz` files from one fold directory:

- `glob(os.path.join(input_folder, model_type, fold_index, '*.npz'))`

([recover_softmax.py:114-140](../../../recover_softmax.py))

The script loads the current DWI and ADC paths from `input/images`, but it reads prediction data from the existing fold outputs in `test_result/`. The recovered softmax arrays are written to:

- `test_result_recover/preliminary_phase/fold0/ISLES22_0001.npz`
- ...
- `test_result_recover/preliminary_phase/fold4/ISLES22_0001.npz`

([recover_softmax.py:107-140](../../../recover_softmax.py))

### Stage 6: Ensembling
`ensemble_predictions.py` reads the five recovered-fold directories, averages the softmax arrays across folds, writes an `.mha`, and optionally stores an ensemble `.npz` ([ensemble_predictions.py:94-137](../../../ensemble_predictions.py)).

With the current launcher arguments, it writes:

- `test_ensemble/ISLES22_0001.mha`
- `test_ensemble/ISLES22_0.npz`

([nnunet_launcher.sh:113-119](../../../nnunet_launcher.sh), [ensemble_predictions.py:104-107](../../../ensemble_predictions.py))

### Stage 7: Final export
`threshold_redirect.py` resolves the current DWI input again, then reads only the first `.mha` file in `test_ensemble/`:

- `pred_file = glob(os.path.join(input_folder, '*.mha'))[0]`

([threshold_redirect.py:95-105](../../../threshold_redirect.py))

It writes the final mask with the basename of the current DWI input path:

- `output/images/stroke-lesion-segmentation/dwi.mha`

and writes `result.json` alongside it ([threshold_redirect.py:112-129](../../../threshold_redirect.py)).

The output filename is therefore stable across runs as long as the DWI input filename remains `dwi.mha`.

## Why the final mask stayed unchanged
The current workspace contains newer converted input files than prediction files:

- `input/images/dwi-brain-mri/dwi.mha` at `2026-04-20 16:53`
- `input/images/adc-brain-mri/adc.mha` at `2026-04-20 16:53`
- `data/.../imagesTs/ISLES22_0001_0000.nii.gz` at `2026-04-20 16:59`
- `data/.../imagesTs/ISLES22_0001_0001.nii.gz` at `2026-04-20 16:59`

But the fold predictions are older:

- `test_result/preliminary_phase/fold0/ISLES22_0001.npz` at `2026-04-20 15:49`
- `test_result/preliminary_phase/fold1/ISLES22_0001.npz` at `2026-04-20 15:49`
- `test_result/preliminary_phase/fold2/ISLES22_0001.npz` at `2026-04-20 15:50`
- `test_result/preliminary_phase/fold3/ISLES22_0001.npz` at `2026-04-20 15:50`
- `test_result/preliminary_phase/fold4/ISLES22_0001.npz` at `2026-04-20 15:50`

The final ensemble and exported mask are newer again:

- `test_ensemble/ISLES22_0001.mha` at `2026-04-20 17:00`
- `output/images/stroke-lesion-segmentation/dwi.mha` at `2026-04-20 17:00`

This timestamp pattern matches the code path:

1. new input was converted into new `imagesTs`
2. the five `nnUNet_predict` stages saw existing `test_result/preliminary_phase/fold*/ISLES22_0001.nii.gz` and `.npz`
3. because `--overwrite_existing` was not passed, those fold predictions were treated as already done
4. `recover_softmax.py`, `ensemble_predictions.py`, and `threshold_redirect.py` then processed the preexisting fold outputs and rewrote the downstream files from old predictions

That is why changing `input/` did not change the final mask in this run.

### Related output-path behavior
Two path conventions reinforce the effect:

- the conversion stage always writes the same case id, `ISLES22_0001` ([Task500_Ischemic_Stroke_Test.py:146-147](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py))
- the final export always writes to `output/images/stroke-lesion-segmentation/dwi.mha` when the input DWI filename is `dwi.mha` ([threshold_redirect.py:116-129](../../../threshold_redirect.py))

So both the intermediate predictions and the final exported file are reused at stable paths unless the prediction stage explicitly regenerates them.

## Code References
- `nnunet_launcher.sh:18-123` - Full orchestration from conversion through final export.
- `nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:125-157` - Resolve raw input and write fixed `ISLES22_0001` test inputs.
- `nnunet/inference/predict_simple.py:102-103` - `--overwrite_existing` defaults to false.
- `nnunet/inference/predict.py:169-179` - Existing output `.nii.gz` and `.npz` files are skipped when overwrite is false.
- `recover_softmax.py:107-140` - Recover fold outputs from `test_result/` into `test_result_recover/`.
- `ensemble_predictions.py:110-137` - Merge recovered folds into `test_ensemble/`.
- `threshold_redirect.py:103-129` - Read the first ensemble `.mha` and export `output/images/stroke-lesion-segmentation/dwi.mha`.

## Architecture Documentation
The repository wraps nnU-Net inference in a fixed single-case staging pipeline. The input case is normalized into a hard-coded `ISLES22_0001` test sample, then passed through five fixed fold directories, then merged into one ensemble output, then copied to a fixed final output filename derived from the DWI input basename.

The prediction stage uses nnU-Net’s built-in existing-output skip behavior. Downstream stages do not independently verify whether the fold predictions were created from the current `input/`; they consume whatever is present under `test_result/`.

## Historical Context (from thoughts/)
- `thoughts/shared/research/2026-04-20-nnunet-launcher-path-assumptions.md` - Earlier documentation of launcher path assumptions and stage-by-stage file flow.
- `thoughts/shared/research/2026-04-20-pytorch-import-failure-context.md` - Earlier documentation of the environment-level torch import failure.
- `thoughts/shared/research/2026-04-20-running-nii-gz-data-with-nnunet-launcher.md` - Earlier notes about running the repo with `.nii.gz` input data.

## Related Research
- [2026-04-20-nnunet-launcher-path-assumptions.md](./2026-04-20-nnunet-launcher-path-assumptions.md)
- [2026-04-20-pytorch-import-failure-context.md](./2026-04-20-pytorch-import-failure-context.md)
- [2026-04-20-running-nii-gz-data-with-nnunet-launcher.md](./2026-04-20-running-nii-gz-data-with-nnunet-launcher.md)

## Open Questions
- Whether the most recent run that produced the `17:00` outputs completed all five fold stages in the same shell session or reused preexisting fold outputs after a partial rerun is not recorded in the files themselves.
