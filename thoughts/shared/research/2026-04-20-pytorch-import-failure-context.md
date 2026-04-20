---
date: 2026-04-20T14:56:24+07:00
researcher: Codex
git_commit: eb2fd3f04396a2f2df6ef0f3e7eeb573c2c253ab
branch: master
repository: ISLES22_SEALS
topic: "PyTorch import failure context in this workspace"
tags: [research, codebase, pytorch, nnunet, environment]
status: complete
last_updated: 2026-04-20
last_updated_by: Codex
---

# Research: PyTorch import failure context in this workspace

**Date**: 2026-04-20T14:56:24+07:00
**Researcher**: Codex
**Git Commit**: `eb2fd3f04396a2f2df6ef0f3e7eeb573c2c253ab`
**Branch**: `master`
**Repository**: `ISLES22_SEALS`

## Research Question
Document the PyTorch import failure context in this workspace. Focus on `requirements.txt`, any pinned torch-related dependencies, and the runtime environment visible from the repo or shell commands. Determine whether the failure happens before model inference and what command in `nnunet_launcher.sh` triggers it.

## Summary

The launcher script runs dataset conversion first, then invokes `nnUNet_predict` five times for folds `0` through `4` ([nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:6), [nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:11)). The `nnUNet_predict` console script imports `nnunet.inference.predict_simple:main`, and `predict_simple.py` imports `torch` at module load time before argument parsing or any call into `predict_from_folder` ([setup.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/setup.py:35), [/mnt/disk1/miniconda3/envs/nnunet/bin/nnUNet_predict](/mnt/disk1/miniconda3/envs/nnunet/bin/nnUNet_predict:1), [predict_simple.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/inference/predict_simple.py:17)).

In this checkout, `requirements.txt` does not pin `torch`, `torchvision`, or `torchaudio`; it only lists other Python packages such as `numpy`, `SimpleITK`, and `batchgenerators` ([requirements.txt](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/requirements.txt:1)). Torch-related version references appear instead in `setup.py`, `nnunet.egg-info`, and the installation instructions in `README.md` ([setup.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/setup.py:11), [nnunet.egg-info/requires.txt](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet.egg-info/requires.txt:1), [README.md](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/README.md:23)).

Shell-visible runtime state shows the active Conda environment is `nnunet` with Python `3.10.14`, `torch 1.11.0`, `torchvision 0.12.0`, `torchaudio 0.11.0`, and `intel-openmp 2025.3.3`. A direct `conda run -n nnunet python -c 'import torch'` reproduces the same failure from the traceback: `ImportError: ... libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent`. This confirms the failure occurs before model inference starts.

## Detailed Findings

### Launcher flow and triggering command

`nnunet_launcher.sh` exports nnUNet path variables, runs dataset conversion, changes the trainer class, then runs `nnUNet_predict` on the test input folder for folds `0` to `4` ([nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:1), [nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:6), [nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:8), [nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:11)).

The first command in the launcher that reaches the PyTorch import path is:

```bash
CUDA_VISIBLE_DEVICES=0 nnUNet_predict \
  -i data/nnUNet_raw_data_base/nnUNet_raw_data/Task500_Ischemic_Stroke_Test/imagesTs/ \
  -o test_result/preliminary_phase/fold0 \
  -t 12 -tr nnUNetTrainerV2_DDP -m 3d_fullres -f 0 -z --disable_postprocessing
```

This corresponds to [nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:11).

The dataset conversion step before it is a plain Python script invocation:

```bash
python nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py
```

([nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:6))

### Where the torch import happens

The editable package definition registers `nnUNet_predict = nnunet.inference.predict_simple:main` as a console script ([setup.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/setup.py:28)). The generated console entrypoint under the Conda environment imports `main` from `nnunet.inference.predict_simple` immediately:

```python
#!/mnt/disk1/miniconda3/envs/nnunet/bin/python3.10
import sys
from nnunet.inference.predict_simple import main
```

([/mnt/disk1/miniconda3/envs/nnunet/bin/nnUNet_predict](/mnt/disk1/miniconda3/envs/nnunet/bin/nnUNet_predict:1))

Inside `predict_simple.py`, `import torch` is at top level on line 17, before `main()` is entered and before the script reaches the later `predict_from_folder(...)` call ([predict_simple.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/inference/predict_simple.py:16), [predict_simple.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/inference/predict_simple.py:25), [predict_simple.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/inference/predict_simple.py:218)).

This places the failure before inference setup, before task-name conversion, and before any model-folder lookup or call to `predict_from_folder`.

### Declared torch-related dependencies in the repo

`requirements.txt` contains pinned versions for packages such as `batchgenerators==0.24`, `numpy==1.21.6`, and `SimpleITK==2.3.1`, but no entries for `torch`, `torchvision`, `torchaudio`, `pytorch`, or `cudatoolkit` ([requirements.txt](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/requirements.txt:1)).

Torch-related declarations and instructions exist in other files:

- `setup.py` declares `torch>1.10.0` in `install_requires` ([setup.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/setup.py:11)).
- `nnunet.egg-info/requires.txt` also records `torch>1.10.0` ([nnunet.egg-info/requires.txt](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet.egg-info/requires.txt:1)).
- `nnunet.egg-info/PKG-INFO` records `Requires-Dist: torch>1.10.0` ([nnunet.egg-info/PKG-INFO](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet.egg-info/PKG-INFO:11)).
- `README.md` instructs users to install `pytorch==1.11.0 torchvision==0.12.0 torchaudio==0.11.0 cudatoolkit=11.3 -c pytorch` before installing the repo ([README.md](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/README.md:23)).

### Runtime environment visible from shell commands

The shell-visible environment and installed packages observed during this research were:

- `conda run -n nnunet python -V` -> `Python 3.10.14`
- `conda run -n nnunet python -c 'import sys; print(sys.executable); print(sys.prefix)'` ->
  `/mnt/disk1/miniconda3/envs/nnunet/bin/python`
  `/mnt/disk1/miniconda3/envs/nnunet`
- `conda run -n nnunet which nnUNet_predict` ->
  `/mnt/disk1/miniconda3/envs/nnunet/bin/nnUNet_predict`
- `conda run -n nnunet python -m pip list | rg '^(torch|torchvision|torchaudio|intel-openmp|numpy|SimpleITK|batchgenerators|nnunet)\s'` reported:
  `batchgenerators 0.24`
  `intel-openmp 2025.3.3`
  `nnunet 1.7.0` (editable project location `/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS`)
  `numpy 1.21.6`
  `SimpleITK 2.3.1`
  `torch 1.11.0`
  `torchaudio 0.11.0`
  `torchvision 0.12.0`

`pip show` adds the same install locations and shows `torch` is installed in `/mnt/disk1/miniconda3/envs/nnunet/lib/python3.10/site-packages` and is required by `nnunet`, `torchaudio`, and `torchvision`.

The environment variables visible from `conda run -n nnunet env` included:

- `CONDA_DEFAULT_ENV=nnunet`
- `CONDA_PREFIX=/mnt/disk1/miniconda3/envs/nnunet`
- `PATH=/mnt/disk1/miniconda3/envs/nnunet/bin:...`

No `LD_LIBRARY_PATH` or `CUDA_*` variables appeared in that `conda run -n nnunet env` output. In the launcher itself, `CUDA_VISIBLE_DEVICES=0` is prepended to each `nnUNet_predict` call ([nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:11)).

### Direct import failure evidence

The direct shell command below reproduces the import failure without running the launcher:

```bash
conda run -n nnunet python -c 'import torch'
```

Observed output:

```text
Traceback (most recent call last):
  File "<string>", line 1, in <module>
  File "/mnt/disk1/miniconda3/envs/nnunet/lib/python3.10/site-packages/torch/__init__.py", line 199, in <module>
    from torch._C import *  # noqa: F403
ImportError: /mnt/disk1/miniconda3/envs/nnunet/lib/python3.10/site-packages/torch/lib/libtorch_cpu.so: undefined symbol: iJIT_NotifyEvent
```

This matches the traceback shown when `bash nnunet_launcher.sh` reaches `nnUNet_predict`.

An additional runtime inspection of the failing shared library with `ldd /mnt/disk1/miniconda3/envs/nnunet/lib/python3.10/site-packages/torch/lib/libtorch_cpu.so` showed it resolving against Conda-provided libraries including `libgomp.so.1`, `libmkl_intel_lp64.so`, `libmkl_gnu_thread.so`, `libmkl_core.so`, and `libcudart.so.11.0`.

### Context from the earlier dataset-conversion failure in the same launcher run

Before the `nnUNet_predict` calls, the launcher runs `python nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py` ([nnunet_launcher.sh](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet_launcher.sh:6)). That script reads `.mha` files from `/input/images/dwi-brain-mri`, `/input/images/adc-brain-mri`, and `/input/images/flair-brain-mri` via `glob(...)[0]` inside `load_data()` ([Task500_Ischemic_Stroke_Test.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:29), [Task500_Ischemic_Stroke_Test.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:34), [Task500_Ischemic_Stroke_Test.py](/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/segmentor/ISLES22_SEALS/nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:125)).

The traceback provided in the user report shows this earlier script fails first with `IndexError: list index out of range`, and the launcher then continues into the `nnUNet_predict` commands because the script does not set `set -e`. The PyTorch import failure therefore appears later in the same launcher run, at the first `nnUNet_predict` invocation.

## Code References

- `requirements.txt:1` - pinned non-torch Python dependencies for the repo
- `setup.py:11` - `install_requires` includes `torch>1.10.0`
- `setup.py:35` - `nnUNet_predict` console script mapping
- `README.md:23` - installation command recommending `pytorch==1.11.0 torchvision==0.12.0 torchaudio==0.11.0 cudatoolkit=11.3`
- `nnunet_launcher.sh:6` - dataset conversion step
- `nnunet_launcher.sh:11` - first `nnUNet_predict` call
- `nnunet/inference/predict_simple.py:17` - top-level `import torch`
- `nnunet/inference/predict_simple.py:25` - `main()` definition begins after import
- `nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py:34` - first `glob(...)[0]` input lookup

## Architecture Documentation

This workspace is installed as editable package `nnunet 1.7.0`, with the repo checkout serving as the editable project location and Conda environment console scripts resolving into the environment’s `bin/` directory. The launcher is a shell script orchestrating a multi-stage test-time pipeline:

1. dataset conversion into `data/nnUNet_raw_data_base`
2. trainer-class update
3. five fold-specific `nnUNet_predict` invocations
4. softmax recovery
5. ensembling
6. threshold redirection into `output/images/stroke-lesion-segmentation/`

Within that pipeline, PyTorch is first touched by `nnUNet_predict`, and the import occurs at module import time rather than later inside an inference function.

## Historical Context (from thoughts/)

No `thoughts/` directory was present in this checkout at the time of research.

## Related Research

No related research documents were present in this checkout before this document was added.

## Open Questions

- The user-provided traceback shows both an earlier dataset-input `IndexError` and the later PyTorch import failure in one launcher run.
- The current research did not inspect external system package managers or non-Conda libraries outside the visible shell commands above.
