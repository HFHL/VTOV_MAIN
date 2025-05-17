#!/bin/bash

# Multiple settings for experiments
# Each setting has its own configuration of model, content_lengths, prompt_ids, and limit

# Base directory for results with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_BASE="experiment_results_${TIMESTAMP}"
mkdir -p "$RESULTS_BASE"

echo "Starting experiments at $(date)"
echo "--------------------------------"

# Function to run experiments with a specified configuration
run_experiment_set() {
    local setting_name=$1
    shift
    local models=($1)
    shift
    local content_lengths=($1)
    shift
    local prompt_ids=($1)
    shift
    local limit=$1
    
    echo "Running experiment set: $setting_name"
    echo "Models: ${models[*]}"
    echo "Content Lengths: ${content_lengths[*]}"
    echo "Prompt IDs: ${prompt_ids[*]}"
    echo "Limit: $limit"
    echo "--------------------------------"
    
    # Create subfolder for this setting
    local setting_dir="${RESULTS_BASE}"
    # local setting_dir="${RESULTS_BASE}/${setting_name}"

    mkdir -p "$setting_dir"
    
    # Loop through all combinations for this setting
    for MODEL in ${models[@]}; do
      for PROMPT_ID in ${prompt_ids[@]}; do
        for LENGTH in ${content_lengths[@]}; do
          echo "Running experiment: Model=$MODEL, Length=$LENGTH, PromptID=$PROMPT_ID"
          
          # Create unique dataset directory for this experiment
          DATASET_DIR="${setting_dir}/${MODEL}_prompt${PROMPT_ID}_${LENGTH}"
          mkdir -p "$DATASET_DIR"
          
          # Run generation
          echo "Generating images..."
          python generate.py --model "$MODEL" --content_length "$LENGTH" --prompt_id "$PROMPT_ID" \
                            --limit "$limit" --dataset_dir "$DATASET_DIR"
          
          if [ $? -ne 0 ]; then
            echo "Error in generation step. Continuing to next experiment."
            continue
          fi
          
          # Run evaluation
          echo "Evaluating results..."
          RESULTS_FILE="${setting_dir}/results_${MODEL}_prompt${PROMPT_ID}_${LENGTH}.json"
          python evaluate.py -i "$DATASET_DIR" -o "$RESULTS_FILE"
          
          if [ $? -ne 0 ]; then
            echo "Error in evaluation step. Continuing to next experiment."
            continue
          fi
          
          echo "Completed: Model=$MODEL, Length=$LENGTH, PromptID=$PROMPT_ID"
          echo "Results saved to $RESULTS_FILE"
          echo "--------------------------------"
        done
      done
    done
    
    # Collect all results and create plots for this setting
    echo "Creating plots for setting: $setting_name"
    
    # For each model and prompt combination, create a plot
    for MODEL in ${models[@]}; do
      for PROMPT_ID in ${prompt_ids[@]}; do
        # Create a list of result files for this model and prompt
        RESULT_FILES=()
        for LENGTH in ${content_lengths[@]}; do
          RESULT_FILE="${setting_dir}/results_${MODEL}_prompt${PROMPT_ID}_${LENGTH}.json"
          if [ -f "$RESULT_FILE" ]; then
            RESULT_FILES+=("$RESULT_FILE")
          fi
        done
        
        # If we have results, run plot.py
        if [ ${#RESULT_FILES[@]} -gt 0 ]; then
          echo "Creating plot for Model=$MODEL, PromptID=$PROMPT_ID"
          PLOT_OUTPUT="${setting_dir}/plot_${MODEL}_prompt${PROMPT_ID}.png"
          python plot.py --input_files "${RESULT_FILES[@]}" --output "${PLOT_OUTPUT}"
        else
          echo "No results available for Model=$MODEL, PromptID=$PROMPT_ID"
        fi
      done
    done
}

# Define different experimental settings

# run_experiment_set "short" "imagen gemini" "50" "4" 1
# run_experiment_set "medium gemini" "gemini" "600" "4" 1
# run_experiment_set "medium imagen" "imagen" "600" "4" 1
# run_experiment_set "long" "imagen gemini" "3000" "4" 1

run_experiment_set "short" "imagen gemini" "50 100 200 300 400" "4" 20
run_experiment_set "medium gemini" "gemini" "600 800 1000 1500 2000" "4" 20
run_experiment_set "medium imagen" "imagen" "600 800 1000 1500 2000" "4" 20
run_experiment_set "long" "imagen gemini" "3000 4000 5000" "4" 5

echo "All experiment sets completed at $(date)"
