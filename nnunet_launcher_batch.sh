set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
shim_so="$script_dir/libjitprofiling_shim.so"
shim_src="$script_dir/jitprofiling_shim.c"
gpu_id="${NNUNET_GPU:-${CUDA_VISIBLE_DEVICES:-0}}"
batch_input_root="${BATCH_INPUT_ROOT:-input}"
task_name="${NNUNET_TASK_NAME:-Task500_Ischemic_Stroke_Test}"
batch_output_root="${BATCH_OUTPUT_ROOT:-output/batch/images/stroke-lesion-segmentation}"
batch_test_result="${BATCH_TEST_RESULT:-test_result_batch}"
batch_test_result_recover="${BATCH_TEST_RESULT_RECOVER:-test_result_recover_batch}"
batch_test_ensemble="${BATCH_TEST_ENSEMBLE:-test_ensemble_batch}"
case_manifest="$script_dir/data/nnUNet_raw_data_base/nnUNet_raw_data/${task_name}/case_manifest.json"

if [ ! -f "$shim_so" ]; then
    gcc -shared -fPIC -O2 "$shim_src" -o "$shim_so"
fi

export LD_PRELOAD="${shim_so}${LD_PRELOAD:+:$LD_PRELOAD}"
export nnUNet_raw_data_base="data/nnUNet_raw_data_base"
export nnUNet_preprocessed="data/nnUNet_preprocessed"
export RESULTS_FOLDER="data/nnUNet_trained_models"
export nnUNet_n_proc_DA=24

python nnunet/dataset_conversion/Task500_Ischemic_Stroke_Test.py \
    --task-name "$task_name" \
    --batch-input-root "$batch_input_root" \
    --case-manifest "$case_manifest"

nnUNet_change_trainer_class -i data/nnUNet_trained_models/nnUNet/3d_fullres/Task012_Ischemic_Stroke_TM_Fullset/nnUNetTrainerV2_DDP__nnUNetPlansv2.1 \
                            -tr nnUNetTrainerV2

for fold in 0 1 2 3 4; do
    CUDA_VISIBLE_DEVICES="$gpu_id" \
    nnUNet_predict \
        -i "$nnUNet_raw_data_base/nnUNet_raw_data/${task_name}/imagesTs/" \
        -o "${batch_test_result}/preliminary_phase/fold${fold}" \
        -t 12 \
        -tr nnUNetTrainerV2_DDP \
        -m 3d_fullres \
        -f "$fold" \
        -z \
        --overwrite_existing \
        --disable_postprocessing
done

for fold in 0 1 2 3 4; do
    python recover_softmax.py \
        -i "${batch_test_result}" \
        -o "${batch_test_result_recover}/preliminary_phase/fold${fold}" \
        -m preliminary_phase \
        -f "fold${fold}" \
        --case-manifest "$case_manifest"
done

python -m ensemble_predictions -f \
    "${batch_test_result_recover}/preliminary_phase/fold0" \
    "${batch_test_result_recover}/preliminary_phase/fold1" \
    "${batch_test_result_recover}/preliminary_phase/fold2" \
    "${batch_test_result_recover}/preliminary_phase/fold3" \
    "${batch_test_result_recover}/preliminary_phase/fold4" \
    -o "${batch_test_ensemble}/" \
    --npz

python threshold_redirect.py \
    -i "${batch_test_ensemble}/" \
    -o "$batch_output_root" \
    --case-manifest "$case_manifest"
