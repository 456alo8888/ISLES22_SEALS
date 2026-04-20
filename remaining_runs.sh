SUBJECTS=$(python - <<'PY'
import csv
with open('/mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/remaining_subjects.csv', newline='') as f:
    print(','.join(row['subject_id'].strip() for row in csv.DictReader(f) if row.get('subject_id', '').strip()))
PY
)

python scripts/prepare_soop_batch_input.py \
  --csv-path /mnt/disk1/hieupc/4gpus-Stroke-outcome-prediction-code/code/utils/SOOP_modalities_dataset.csv \
  --output-root input_remaining \
  --subjects "$SUBJECTS"


BATCH_INPUT_ROOT=input_remaining \
BATCH_TEST_RESULT=test_result_resume \
BATCH_TEST_RESULT_RECOVER=test_result_recover_resume \
BATCH_TEST_ENSEMBLE=test_ensemble_resume \
BATCH_OUTPUT_ROOT=output/batch_resume/images/stroke-lesion-segmentation \
NNUNET_GPU=0 \
bash nnunet_launcher_batch.sh

