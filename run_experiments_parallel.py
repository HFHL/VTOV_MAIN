import os
import json
import time
import argparse
import concurrent.futures
from datetime import datetime
import subprocess
import re
from collections import defaultdict
from pathlib import Path

def create_results_directory():
    """Create a timestamp-based results directory"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_base = f"experiment_results_{timestamp}"
    os.makedirs(results_base, exist_ok=True)
    print(f"Created results directory: {results_base}")
    return results_base

def extract_language_code(input_file):
    """Extract language code from input file name"""
    match = re.search(r"^[^_]+_([^_]+)_", input_file)
    if match:
        return match.group(1)
    return "en"

def map_tesseract_lang(lang_code):
    """Map language code to Tesseract OCR language code"""
    lang_map = {
        "en": "eng",
        "fr": "fra",
        "zh": "chi_sim+chi_tra"
    }
    return lang_map.get(lang_code, "eng")

def map_paddleocr_lang(lang_code):
    lang_map = {
        "en": "en",
        "zh": "ch",
        "fr": "fr"
    }
    return lang_map.get(lang_code, "en")

def run_generation_task(model, length, dataset_dir, input_file, limit, thread_id, total_threads):
    """Run a single generation task with a subset of records"""
    
    # Calculate the range of records this thread should process
    # Use ceiling division for first n-1 threads, then adjust the last thread
    # to ensure the total equals exactly the limit
    if total_threads == 1:
        # If only one thread, process all records
        records_per_thread = limit
        start_idx = 0
        end_idx = limit
    else:
        # For multiple threads, distribute evenly
        base_records_per_thread = limit // total_threads
        remainder = limit % total_threads
        
        # First 'remainder' threads get one extra record
        if thread_id < remainder:
            records_for_this_thread = base_records_per_thread + 1
            start_idx = thread_id * records_for_this_thread
        else:
            records_for_this_thread = base_records_per_thread
            start_idx = (remainder * (base_records_per_thread + 1)) + ((thread_id - remainder) * base_records_per_thread)
        
        end_idx = start_idx + records_for_this_thread

    
    # Create a temporary subdirectory for this thread
    thread_dataset_dir = f"{dataset_dir}/thread_{thread_id}"
    os.makedirs(thread_dataset_dir, exist_ok=True)

    print(f"Thread {thread_id}: Running generation for Model={model}, Length={length}, Start Index={start_idx}, End Index={end_idx}, Total Records={end_idx - start_idx}. Dataset dir: {thread_dataset_dir}")
    
    # Prepare command
    cmd = [
        "python", "generate.py",
        "--model", model,
        "--content_length", str(length),
        "--limit", str(end_idx - start_idx),
        "--start_idx", str(start_idx),
        "--dataset_dir", thread_dataset_dir,
        "--file_path", input_file
    ]
    
    # Run command
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Thread {thread_id}: Completed {model}_{length} task")
        print(result.stdout)
        return {
            "success": True,
            "thread_id": thread_id,
            "model": model,
            "length": length,
            "thread_dataset_dir": thread_dataset_dir,
            "output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        print(f"Thread {thread_id}: ERROR running {model}_{length} task: {e}")
        return {
            "success": False,
            "thread_id": thread_id,
            "model": model,
            "length": length,
            "thread_dataset_dir": thread_dataset_dir,
            "error": str(e),
            "output": e.stdout if e.stdout else ""
        }

def merge_thread_results(results, dataset_dir):
    """Merge results from all threads into the main dataset directory and clean up thread directories"""
    for result in results:
        if result["success"]:
            thread_dir = result["thread_dataset_dir"]
            # Copy all files from thread directory to main directory
            for filename in os.listdir(thread_dir):
                src_path = os.path.join(thread_dir, filename)
                dst_path = os.path.join(dataset_dir, filename)
                
                # Skip directories and only copy files
                if os.path.isfile(src_path):
                    # Read source file
                    with open(src_path, "rb") as src_file:
                        content = src_file.read()
                    
                    # Write to destination file
                    with open(dst_path, "wb") as dst_file:
                        dst_file.write(content)
                    
                    # Delete the source file after successful copy
                    os.remove(src_path)
            
            # Remove the empty thread directory
            try:
                os.rmdir(thread_dir)
                print(f"Cleaned up thread directory: {thread_dir}")
            except OSError as e:
                print(f"Warning: Could not remove thread directory {thread_dir}: {str(e)}")


def run_experiment_set(setting_name, models, content_lengths, limit, input_file, num_threads, results_base):
    """Run experiments with the specified configuration in parallel"""
    
    # Process language settings
    lang_code = extract_language_code(input_file)
    # tesseract_lang = map_tesseract_lang(lang_code)
    paddleocr_lang = map_paddleocr_lang(lang_code)
    
    # Create setting directory
    input_file_name = os.path.splitext(os.path.basename(input_file))[0]
    setting_dir = os.path.join(results_base, input_file_name)
    os.makedirs(setting_dir, exist_ok=True)
    
    print(f"Running experiment set: {setting_name}")
    print(f"Models: {' '.join(models)}")
    print(f"Content Lengths: {' '.join(map(str, content_lengths))}")
    print(f"Limit: {limit}")
    print(f"Input File: {input_file}")
    # print(f"Language Code: {lang_code} (Tesseract: {tesseract_lang})")
    print(f"Language Code: {lang_code} (PaddleOCR: {paddleocr_lang})")
    
    print(f"Using {num_threads} threads")
    print("--------------------------------")
    
    # Process each model and length combination
    for model in models:
        for length in content_lengths:
            print(f"\nProcessing: Model={model}, Length={length}")
            
            # Create dataset directory
            dataset_dir = os.path.join(setting_dir, f"{model}_{length}")
            os.makedirs(dataset_dir, exist_ok=True)
            
            # Create tasks for parallel execution
            tasks = []
            for thread_id in range(num_threads):
                tasks.append((model, length, dataset_dir, input_file, limit, thread_id, num_threads))
            
            # Execute tasks in parallel
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                future_to_task = {
                    executor.submit(run_generation_task, *task): task for task in tasks
                }
                
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as exc:
                        print(f"Task generated an exception: {exc}")
                        results.append({
                            "success": False,
                            "thread_id": task[5],
                            "model": task[0],
                            "length": task[1],
                            "error": str(exc)
                        })
            
            # Merge results from all threads
            merge_thread_results(results, dataset_dir)
            
            # Run evaluation
            print(f"Evaluating results for Model={model}, Length={length}")
            results_file = os.path.join(setting_dir, f"results_{model}_{length}.json")
            
            try:
                eval_cmd = [
                    "python", "evaluate.py",
                    "-i", dataset_dir,
                    "-o", results_file,
                    "-l", paddleocr_lang
                    # "-l", tesseract_lang
                ]
                subprocess.run(eval_cmd, check=True)
                print(f"Evaluation completed: {results_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error in evaluation step: {e}")
    
    
    print(f"Experiment set '{setting_name}' completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return setting_dir

def plot_consolidated_results(results_dirs):
    """Generate consolidated plots for all results, grouped by model and language"""
    print("\n=== Generating consolidated plots across all experiments ===")
    print(results_dirs)
    # Structure to store all result files by model and language
    # {model: {language: [(length, result_file_path), ...], ...}, ...}
    grouped_files = defaultdict(lambda: defaultdict(list))
    
    # Collect all result files and group them
    for results_dir in results_dirs:
        for file in os.listdir(results_dir):
            if file.startswith("results_") and file.endswith(".json"):
                # Extract model, length from filename
                match = re.match(r'results_([a-z]+)_([0-9]+)\.json', file)
                if match:
                    model = match.group(1)
                    length = int(match.group(2))
                    
                    # Extract language from dir_name (wikipedia_LANG_...)
                    lang_match = re.search(r'wikipedia_([a-z]{2})_', results_dir)
                    if lang_match:
                        language = lang_match.group(1)
                        result_path = os.path.join(results_dir, file)
                        grouped_files[model][language].append((length, result_path))
    
    # Generate consolidated plots for each model and language
    for model, languages in grouped_files.items():
        for language, files_info in languages.items():
            if len(files_info) > 1:  # Only plot if we have multiple lengths
                print(f"Creating consolidated plot for Model={model}, Language={language}")
                
                # Sort by length for better visualization
                files_info.sort(key=lambda x: x[0])
                result_files = [file_path for _, file_path in files_info]
                
                # Create plot output path
                plot_dir = os.path.join(os.path.dirname(results_dirs[0]), "consolidated_plots")
                os.makedirs(plot_dir, exist_ok=True)
                plot_output = os.path.join(plot_dir, f"plot_{model}_{language}_by_length.png")
                
                try:
                    # Create the plot command
                    plot_cmd = ["python", "plot.py", "--output", plot_output]
                    
                    if result_files:  # Make sure there's at least one file
                        plot_cmd.append("--input_files")
                        # Add each file as a separate argument
                        for file in result_files:
                            plot_cmd.append(file)
                    
                    print(f"Running plot command: {' '.join(plot_cmd)}")
                    subprocess.run(plot_cmd, check=True)
                    print(f"Consolidated plot created: {plot_output}")
                except subprocess.CalledProcessError as e:
                    print(f"Error creating consolidated plot: {e}")
    
    print("Consolidated plotting completed")

def evaluate_only(args):
    print(f"Starting evaluation for path: {args.evaluate_only_experiment_path}")

    assert args.ocr_engine in ["paddleocr", "tesseract"], "Invalid OCR engine specified. Must be 'paddleocr' or 'tesseract'."

    print(f"Using OCR engine: {args.ocr_engine}")

    # Use os.walk to traverse the nested directory structure
    for root, dirs, files in os.walk(args.evaluate_only_experiment_path):
        # Looking for the leaf directories that contain the images and text files.
        if not any(f.endswith('.png') for f in files):
            continue

        # 'root' is now the target directory, e.g., .../{model}_{length}/
        results_dir = root
        print(f"Processing directory: {results_dir}")

        # Extract the language code directly from the directory structure.
        # The parent of the 'results_dir' is the language code directory.
        try:
            language = Path(results_dir).parent.name
            print(f"Language '{language}' detected from path.")
        except IndexError:
            print(f"Could not determine language for {results_dir}. Skipping.")
            continue

        # Define the output file path within the results directory
        results_file = os.path.join(results_dir, "results_paddleocr.json")

        # Map the detected language to the format required by PaddleOCR
        if args.ocr_engine == "paddleocr":
            ocr_lang = map_paddleocr_lang(language)
        elif args.ocr_engine == "tesseract":
            ocr_lang = map_tesseract_lang(language)

        # Construct the evaluation command
        eval_cmd = [
            "python", "evaluate.py",
            "-i", results_dir,
            "-o", results_file,
            "-l", ocr_lang,
            "-e", args.ocr_engine,
        ]

        # Run the evaluation command
        try:
            subprocess.run(eval_cmd, check=True, capture_output=True, text=True)
            print(f"Evaluation completed for {language}: {results_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error evaluating {results_dir}:")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")

def main():
    """Main function to parse command line arguments and run experiments"""
    parser = argparse.ArgumentParser(description="Run text-to-image generation experiments in parallel")
    parser.add_argument("--settings", type=str, default="all",
                        help="Comma-separated list of settings to run (e.g., 'short,long' or 'all')")
    parser.add_argument("--threads", type=int, default=4,
                        help="Number of threads to use for parallel processing")
    parser.add_argument("--config", type=str, default="experiment_config.json",
                        help="Path to experiment configuration file")
    parser.add_argument("--skip_plot", action="store_true",
                        help="Skip generating consolidated plots")
    parser.add_argument("--plot_only_experiment_path", type=str, default=None,
                        help="Path to directory containing result files to plot")
    parser.add_argument("--evaluate_only_experiment_path", type=str, default=None,
                        help="Path to directory containing result files to evaluate")
    parser.add_argument("--ocr_engine", type=str, default="paddleocr")
    args = parser.parse_args()

    # If plot_only_experiment_path is provided, only plot the results in that directory
    if args.plot_only_experiment_path:
        # structure
        # Inputs: plot_only_experiment_path/wikipedia_{LANG}_*/{model}_{length}/evaluation_results.json
        # Outputs: plot_only_experiment_path/consolidated_plots/
        results_dirs = [os.path.join(args.plot_only_experiment_path, d) for d in os.listdir(args.plot_only_experiment_path) if d.startswith("wikipedia_")]
        plot_consolidated_results(results_dirs)
        return
    
    if args.evaluate_only_experiment_path:
        # Structure: evaluate_only_experiment_path/{model}/{language_code}/{model}_{length}/*.{png,txt}
        # Output: evaluate_only_experiment_path/{model}/{language_code}/{model}_{length}/results_paddleocr.json
        evaluate_only(args)
        return
    
    # Load experiment configuration
    with open(args.config, "r") as f:
        config = json.load(f)

    # Determine settings to run
    settings_to_run = []
    if args.settings.lower() == "all":
        settings_to_run = list(config.keys())
    else:
        settings_to_run = [s.strip() for s in args.settings.split(",")]
    
    results_base = create_results_directory()
    
    print(f"Starting experiments at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("--------------------------------")

    # Run selected experiment settings
    results_dirs = []
    for setting in settings_to_run:
        if setting in config:
            setting_config = config[setting]
            
            for input_file in setting_config["input_files"]:
                print(f"\n=== Running {setting} experiments with {input_file} ===\n")
                results_dir = run_experiment_set(
                    setting,
                    setting_config["models"],
                    setting_config["content_lengths"],
                    setting_config["limit"],
                    input_file,
                    args.threads,
                    results_base
                )
                results_dirs.append(results_dir)
        else:
            print(f"Warning: Setting '{setting}' not found in configuration")
    
    print("\nAll experiment sets completed")
    print(f"Results saved in: {', '.join(results_dirs)}")
    
    # Generate consolidated plots if not skipped
    if not args.skip_plot:
        plot_consolidated_results(results_dirs)

if __name__ == "__main__":
    start_time = time.time()
    main()
    elapsed_time = time.time() - start_time
    print(f"\nTotal execution time: {elapsed_time:.2f} seconds")
