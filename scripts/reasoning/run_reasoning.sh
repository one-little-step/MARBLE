SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_DIR" || exit 1

WORKSPACE_DIR="marble/workspace"
UPDATE_SCRIPT="scripts/reasoning/update_reasoning_config.py"
BASE_CONFIG_DIR="marble/configs"

CONFIG_PATHS=(
    "${BASE_CONFIG_DIR}/test_config_reasoning_reflexion.yaml"
    "${BASE_CONFIG_DIR}/test_config_reasoning_react.yaml"
    "${BASE_CONFIG_DIR}/test_config_reasoning_cot.yaml"
)

model_name="gpt-3.5-turbo"
safe_model_name=$(echo ${model_name} | tr '/' '_')
BASE_LOG_DIR="marble/logs/${safe_model_name}"

mkdir -p result

for config_path in "${CONFIG_PATHS[@]}"; do
    method_name=$(basename ${config_path} .yaml | sed 's/test_config_reasoning_//')
    LOG_DIR="${BASE_LOG_DIR}/${method_name}"
    mkdir -p ${LOG_DIR}

    echo "Starting experiments with ${method_name}..."

    for id in {1..10}; do
        echo "Processing ${method_name} task with ID=$id..."
        rm -rf ${WORKSPACE_DIR}/*
        python ${UPDATE_SCRIPT} ${id} --config ${config_path}
        echo "Running the demo script..."
        python marble/main.py --config ${config_path}
        echo "Saving solution file..."
        cp ${WORKSPACE_DIR}/solution.py ${LOG_DIR}/solution_${id}.py
        echo "Task with ID=$id completed."
        echo "==============================="
    done

    echo "Copying result file for ${method_name}..."
    cp marble/result/development_output.jsonl marble/result/${method_name}_output.jsonl
    rm marble/result/development_output.jsonl

    echo "${method_name} experiments completed!"
    echo "==============================="
done

echo "All experiments have been completed!"
