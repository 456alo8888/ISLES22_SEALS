---
date: 2026-04-20T15:10:00+07:00
researcher: Codex
git_commit: eb2fd3f04396a2f2df6ef0f3e7eeb573c2c253ab
branch: master
repository: ISLES22_SEALS
topic: "How to run nnunet_launcher.sh on user data with .nii.gz inputs"
tags: [research, codebase, nnunet, isles22, data-ingestion]
status: complete
last_updated: 2026-04-20
last_updated_by: Codex
---

# Research: How to run nnunet_launcher.sh on user data with .nii.gz inputs

**Date**: 2026-04-20T15:10:00+07:00  
**Researcher**: Codex  
**Git Commit**: eb2fd3f04396a2f2df6ef0f3e7eeb573c2c253ab  
**Branch**: master  
**Repository**: ISLES22_SEALS

## Research Question
Read nnunet_launcher.sh and explain how to run the model on user data when the source dataset is .nii.gz, including which directories are used and what preprocessing is required.

## Summary
The current inference pipeline in this repository expects ISLES inputs in .mha format under modality folders, not .nii.gz. The input root is resolved from /input/images first, then input/images. Required modality folders are dwi-brain-mri and adc-brain-mri, with flair-brain-mri optional. The launcher calls a conversion script that reads .mha and writes nnU-Net test images as .nii.gz into Task500 imagesTs, then runs five-fold prediction, softmax recovery, ensembling, and final output export.

## Detailed Findings

### Launcher orchestration
- The launcher sets nnU-Net env vars and runs dataset conversion first, then prediction folds, recovery, ensemble, and threshold redirect: [nnunet_launcher.sh](../../../nnunet_launcher.sh#L13), [nnunet_launcher.sh](../../../nnunet_launcher.sh#L18), [nnunet_launcher.sh](../../../nnunet_launcher.sh#L23), [nnunet_launcher.sh](../../../nnunet_launcher.sh#L78), [nnunet_launcher.sh](../../../nnunet_launcher.sh#L113), [nnunet_launcher.sh](../../../nnunet_launcher.sh#L121).
- Prediction input path used by all five folds is data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs: [nnunet_launcher.sh](../../../nnunet_launcher.sh#L25).

### Input root and file format expectations
- Input root resolver checks /input/images then input/images: [nnunet/isles22_input.py](../../../nnunet/isles22_input.py#L5).
- Required and optional modality lookups use *.mha glob patterns: [nnunet/isles22_input.py](../../../nnunet/isles22_input.py#L16), [nnunet/isles22_input.py](../../../nnunet/isles22_input.py#L25).
- The conversion script uses these modality folders: dwi-brain-mri, adc-brain-mri, flair-brain-mri: [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py#L30).

### What preprocessing is done by code
- DWI is respaced to 1x1x1 and ADC is resized to DWI geometry before writing nnU-Net inputs: [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py#L142), [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py#L143).
- Converted outputs are written as ISLES22_0001_0000.nii.gz and ISLES22_0001_0001.nii.gz in imagesTs: [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py#L146).

### Post-prediction format flow
- Recovery reads fold .npz outputs and rebuilds softmax aligned to input geometry: [recover_softmax.py](../../../recover_softmax.py#L113).
- Ensemble reads recovered .npz and writes per-case .mha prediction in test_ensemble: [ensemble_predictions.py](../../../ensemble_predictions.py#L120), [ensemble_predictions.py](../../../ensemble_predictions.py#L133).
- Final output writer reads test_ensemble .mha and writes to output/images/stroke-lesion-segmentation: [threshold_redirect.py](../../../threshold_redirect.py#L104), [threshold_redirect.py](../../../threshold_redirect.py#L116).

## Code References
- nnunet_launcher.sh:13 - nnU-Net path env exports.
- nnunet_launcher.sh:18 - dataset conversion call.
- nnunet_launcher.sh:25 - nnUNet_predict input directory.
- nnunet/isles22_input.py:5 - input root candidates.
- nnunet/isles22_input.py:16 - required image extension is .mha.
- nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:30 - modality folder names.
- nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:146 - writes .nii.gz files for Task500 imagesTs.
- recover_softmax.py:113 - reads fold npz outputs.
- ensemble_predictions.py:133 - writes ensembled .mha.
- threshold_redirect.py:116 - writes final output file.

## Architecture Documentation
Current data path through the system:
1. Source input under /input/images or input/images, modality folders, .mha files.
2. Conversion step writes Task500 test set in nnU-Net internal .nii.gz naming.
3. Five nnUNet_predict runs produce fold outputs in test_result/preliminary_phase/fold0..4.
4. recover_softmax.py rewrites fold softmax to test_result_recover/preliminary_phase/fold0..4.
5. ensemble_predictions.py merges recovered folds into test_ensemble.
6. threshold_redirect.py writes final segmentation and result.json under output/images/stroke-lesion-segmentation.

## Historical Context (from thoughts/)
- thoughts/shared/research/2026-04-20-nnunet-launcher-path-assumptions.md - prior documentation of launcher path assumptions and stage outputs.
- thoughts/shared/research/2026-04-20-pytorch-import-failure-context.md - prior documentation of torch import failure timing in the launcher sequence.

## Related Research
- thoughts/shared/research/2026-04-20-nnunet-launcher-path-assumptions.md
- thoughts/shared/research/2026-04-20-pytorch-import-failure-context.md

## Open Questions
- The current converter writes one fixed test case id (ISLES22_0001) in this script version.
