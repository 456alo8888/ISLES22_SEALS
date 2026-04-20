# SOOP Batch Input Staging And Batch Segmentation Plan

## Overview

This plan is scoped in two layers:

1. Phase 1 implements only CSV-driven staging of subject inputs from SOOP `.nii.gz` files into per-subject `.mha` folders using the existing `sub-xxxx` identifiers.
2. Later phases define the repo changes needed so the staged subject folders can be segmented in batch by this codebase instead of the current single-subject flow.

The immediate deliverable is a script that reads `/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv`, uses each row’s `trace_path` and `adc_path`, and writes:

```text
input/
  sub-100/
    dwi-brain-mri/dwi.mha
    adc-brain-mri/adc.mha
  sub-1001/
    dwi-brain-mri/dwi.mha
    adc-brain-mri/adc.mha
```

## Current State Analysis

The current repo expects raw inputs as `.mha` files under a single global input root. `resolve_input_root()` only checks `/input/images` and `input/images`, and modality lookup requires `*.mha` inside `dwi-brain-mri` and `adc-brain-mri` ([nnunet/isles22_input.py:5](../../../nnunet/isles22_input.py), [nnunet/isles22_input.py:15](../../../nnunet/isles22_input.py)).

The current dataset conversion stage loads one DWI and one ADC, then writes a single fixed test case into nnU-Net `imagesTs` as `ISLES22_0001_0000.nii.gz` and `ISLES22_0001_0001.nii.gz` ([nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:125](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py), [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:146](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py), [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:147](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)).

The launcher orchestrates one linear single-case workflow: dataset conversion, five fold predictions, softmax recovery, ensemble, and final export ([nnunet_launcher.sh:18](../../../nnunet_launcher.sh), [nnunet_launcher.sh:23](../../../nnunet_launcher.sh), [nnunet_launcher.sh:78](../../../nnunet_launcher.sh), [nnunet_launcher.sh:113](../../../nnunet_launcher.sh), [nnunet_launcher.sh:121](../../../nnunet_launcher.sh)).

There is already a working conversion pattern in `transfer.ipynb`: read a `.nii.gz` with `sitk.ReadImage` and write `.mha` with `sitk.WriteImage`, preserving image metadata ([transfer.ipynb](../../../transfer.ipynb)). The notebook writes directly to this repo’s expected DWI and ADC `.mha` filenames.

The source CSV already has the needed columns for staging:

- `subject_id`
- `trace_path`
- `adc_path`
- `has_trace`
- `has_adc`

([/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv:1](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv:1))

## Desired End State

After Phase 1:

- A dedicated staging script reads the SOOP CSV.
- Eligible rows are filtered using `subject_id`, `trace_path`, `adc_path`, `has_trace`, and `has_adc`.
- Each eligible subject gets a directory under a chosen output root using the original `subject_id`, not a normalized `case001` id.
- Each subject directory contains:

```text
<output_root>/sub-xxxx/dwi-brain-mri/dwi.mha
<output_root>/sub-xxxx/adc-brain-mri/adc.mha
```

- `.mha` outputs preserve the source image metadata by using SimpleITK read/write.
- The script emits a manifest or summary log describing which subjects were converted, skipped, or failed.

After later batch-segmentation phases:

- The repo can enumerate staged subject folders.
- The conversion step can turn each staged subject into a distinct nnU-Net test case rather than always `ISLES22_0001`.
- Downstream prediction recovery, ensemble, and final export can preserve per-subject identity end to end.

### Key Discoveries

- The current input contract is single-root and `.mha`-based: [nnunet/isles22_input.py:5-26](../../../nnunet/isles22_input.py).
- The current converter is single-case and hardcodes `ISLES22_0001`: [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:125-157](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py).
- Existing notebook code already demonstrates `.nii.gz` to `.mha` conversion using SimpleITK: [transfer.ipynb](../../../transfer.ipynb).
- Downstream batch support does not exist yet in `recover_softmax.py` and `threshold_redirect.py`, both of which assume one current input case: [recover_softmax.py:107-140](../../../recover_softmax.py), [threshold_redirect.py:95-129](../../../threshold_redirect.py).

## What We're NOT Doing

For Phase 1:

- We are not changing `nnunet_launcher.sh` to process multiple subjects yet.
- We are not changing `nnunet/isles22_input.py` to read `input/sub-xxxx/...` trees yet.
- We are not changing `Task500_Ischemic_Stroke_Test.py` to emit multiple `imagesTs` cases yet.
- We are not adding FLAIR handling to the staging script.
- We are not changing model weights, trainer configuration, or inference hyperparameters.

For the later integration plan section:

- We are not implementing the batch segmentation changes in this phase.
- We are only specifying how they should be structured and verified.

## Implementation Approach

Phase 1 should be implemented as a standalone staging script, separate from the current launcher. The script should be driven by the CSV, convert source `.nii.gz` files to `.mha` using the existing SimpleITK pattern, and write the staged directories using the CSV’s `subject_id` directly.

This keeps the first phase isolated from the current single-subject inference pipeline and makes it easy to verify the staged inputs before any nnU-Net integration work.

The later batch segmentation work should then adapt the existing repo around that staged contract instead of inventing a second staging convention.

## Phase 1: CSV-Driven Subject Staging

### Overview

Create a script that reads the SOOP CSV and prepares per-subject `.mha` input folders using the existing `sub-xxxx` identifiers.

### Changes Required:

#### 1. Add A Dedicated Staging Script
**File**: `scripts/prepare_soop_batch_input.py` or equivalent new utility module under the repo root
**Changes**:
- Parse the CSV from `/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv`
- Read at minimum:
  - `subject_id`
  - `trace_path`
  - `adc_path`
  - `has_trace`
  - `has_adc`
- Filter to rows eligible for DWI+ADC staging
- For each eligible subject, create:
  - `input/<subject_id>/dwi-brain-mri/`
  - `input/<subject_id>/adc-brain-mri/`
- Convert:
  - `trace_path` -> `input/<subject_id>/dwi-brain-mri/dwi.mha`
  - `adc_path` -> `input/<subject_id>/adc-brain-mri/adc.mha`
- Use the SimpleITK conversion pattern already demonstrated in `transfer.ipynb`
- Record per-subject outcomes for success, skip, and failure cases

```python
# intended conversion shape
img = sitk.ReadImage(input_path)
sitk.WriteImage(img, output_path)
```

#### 2. Define CLI And Logging Contract
**File**: `scripts/prepare_soop_batch_input.py`
**Changes**:
- Support CLI flags for:
  - input CSV path
  - output root path
  - optional subject subset
  - overwrite policy
  - dry-run mode
- Emit a summary at the end:
  - total rows read
  - total eligible rows
  - subjects converted
  - subjects skipped
  - subjects failed
- Write a manifest CSV or JSON beside the output root so later segmentation phases can reuse the same case list

#### 3. Add Documentation For Staged Layout
**File**: `README.md` or a dedicated usage doc under `thoughts/shared/research/`
**Changes**:
- Document the intended staging tree using `sub-xxxx`
- Document the source CSV columns used
- Document the exact command used to generate staged input

### Success Criteria:

#### Automated Verification:
- [x] The staging script runs without import errors: `python scripts/prepare_soop_batch_input.py --help`
- [x] For a controlled subset of subjects, the output directories exist:
  - `input/sub-xxxx/dwi-brain-mri/dwi.mha`
  - `input/sub-xxxx/adc-brain-mri/adc.mha`
- [x] Output `.mha` files are readable with SimpleITK: `python -c "import SimpleITK as sitk; sitk.ReadImage('.../dwi.mha')"`
- [x] The manifest file is produced and lists converted subjects

#### Manual Verification:
- [ ] Spot-check at least one subject’s DWI `.mha` against its source `.nii.gz`
- [ ] Spot-check at least one subject’s ADC `.mha` against its source `.nii.gz`
- [ ] Folder names exactly match the CSV `subject_id` values
- [ ] The staged folder tree matches the required modality naming

**Implementation Note**: After Phase 1 is complete and automated checks pass, pause for manual confirmation that the staged `.mha` outputs look correct before moving to any integration work.

---

## Phase 2: Verification Utilities For Staged Data

### Overview

Add lightweight validation helpers so staged subject inputs can be checked before attempting batch inference integration.

### Changes Required:

#### 1. Add Validation Command Or Helper
**File**: `scripts/validate_soop_batch_input.py` or a validation mode in the staging script
**Changes**:
- Read staged subject directories
- Confirm both `dwi.mha` and `adc.mha` exist for each expected subject
- Confirm files are readable
- Optionally compare source `.nii.gz` and staged `.mha` shapes, spacing, origin, and direction

#### 2. Reuse Existing Validation Pattern
**File**: `test_plot.ipynb` references and validation helper
**Changes**:
- Follow the existing pattern already used locally for comparing source and converted data
- Keep the validation script non-destructive and focused on staging integrity

### Success Criteria:

#### Automated Verification:
- [x] Validation script exits successfully on a known-good staged subset
- [ ] Validation script reports missing or unreadable files when given a broken subject folder

#### Manual Verification:
- [ ] At least one subject is visually inspected in both source and staged formats
- [ ] The validator output is understandable enough to be used before batch segmentation

---

## Phase 3: Batch Segmentation Script Plan

### Overview

Plan the script and repo changes required so the staged `input/sub-xxxx/...` folders can be segmented in batch by this codebase.

### Changes Required:

#### 1. Extend Input Discovery Beyond `input/images`
**File**: `nnunet/isles22_input.py`
**Changes**:
- Add a subject-enumeration layer that can discover many subject folders under a batch input root
- Preserve the existing modality subfolder names:
  - `dwi-brain-mri`
  - `adc-brain-mri`
- Separate single-case helper behavior from batch enumeration behavior

#### 2. Replace Single-Case Dataset Conversion
**File**: `nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py`
**Changes**:
- Replace the single `dataset_ISLES22.load_data()` assumption with iteration over staged subjects
- For each subject, write:
  - `<case_id>_0000.nii.gz`
  - `<case_id>_0001.nii.gz`
- Preserve subject identity instead of always using `ISLES22_0001`
- Ensure `dataset.json` remains consistent with many test cases

#### 3. Batch-Aware Recovery
**File**: `recover_softmax.py`
**Changes**:
- Replace the single current DWI/ADC geometry assumption with per-subject geometry lookup
- Map each `.npz` prediction back to the correct staged subject geometry

#### 4. Batch-Aware Final Export
**File**: `threshold_redirect.py`
**Changes**:
- Replace the first-file-only `glob(...)[0]` export behavior
- Write one final output mask per subject
- Build a multi-entry result manifest rather than one `result.json` item

#### 5. Add A Batch Launcher
**File**: `nnunet_launcher_batch.sh` or equivalent
**Changes**:
- Keep the current single-subject launcher intact
- Add a separate batch launcher or batch mode that:
  - uses the staged subject root
  - runs the multi-case dataset conversion
  - runs nnU-Net prediction once across the multi-case `imagesTs`
  - performs batch recovery, ensemble, and export

### Success Criteria:

#### Automated Verification:
- [x] Multi-case `imagesTs` contains one `_0000` and one `_0001` file per staged subject
- [ ] `nnUNet_predict` sees multiple unique case ids in one run
- [ ] Recovered fold outputs preserve one `.npz` per case per fold
- [x] Final output contains one exported mask per subject

#### Manual Verification:
- [ ] At least two subjects can be traced end-to-end from staged input to final exported mask
- [ ] Subject identity remains consistent between CSV, staged folder, `imagesTs`, fold outputs, ensemble output, and final mask
- [ ] Final output organization is usable for downstream analysis

**Implementation Note**: This phase should not begin until the staged-input contract from Phase 1 has been validated on a real subset.

---

## Testing Strategy

### Unit Tests:
- CSV row filtering behavior for valid and invalid modality rows
- Subject-id handling using original `sub-xxxx` values
- Output path construction for DWI and ADC `.mha` files
- Manifest generation for converted and skipped subjects

### Integration Tests:
- Run staging on a small subset of known-good subjects
- Verify resulting folder tree and file readability
- Later, run multi-case dataset conversion on a staged subset and verify `imagesTs` output naming

### Manual Testing Steps:
1. Pick 2-3 subjects from the CSV with valid TRACE and ADC paths.
2. Run the staging script on only those subjects.
3. Inspect the output folders under `input/sub-xxxx/`.
4. Open the staged `.mha` files and compare them against the original `.nii.gz` inputs.
5. Confirm the same subject ids can be used consistently in later batch integration work.

## Performance Considerations

Phase 1 is I/O-bound and dominated by reading and rewriting medical volumes. The script should be written so it can safely process large CSVs and optionally subset subjects for debugging.

For later batch segmentation work, the main constraint is not staging throughput but adapting the current single-case pipeline to preserve per-subject identity through conversion, prediction, recovery, and export.

## Migration Notes

No migration is required for existing single-subject usage if the staging script is added as a separate utility and the current single-subject launcher remains unchanged.

For later batch segmentation support, a separate batch entrypoint is preferable so the current `input/images` workflow stays available.

## References

- Source CSV: `/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv`
- Current input contract: [nnunet/isles22_input.py](../../../nnunet/isles22_input.py)
- Current single-case conversion: [nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py](../../../nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py)
- Current launcher: [nnunet_launcher.sh](../../../nnunet_launcher.sh)
- Current recovery/export flow: [recover_softmax.py](../../../recover_softmax.py), [threshold_redirect.py](../../../threshold_redirect.py)
- Existing `.nii.gz` to `.mha` example: [transfer.ipynb](../../../transfer.ipynb)
