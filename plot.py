#!/usr/bin/env python3
import os
import json
import re
import argparse
import matplotlib.pyplot as plt
import numpy as np

def extract_filename_info(filename):
    """Extract model, prompt ID and context length from the filename."""
    # Match patterns like results_imagen_prompt0_1000.json
    match = re.search(r'results_([a-z]+)_prompt(\d+)_(\d+)\.json', filename)
    if match:
        model = match.group(1)
        prompt_id = int(match.group(2))
        context_length = int(match.group(3))
        return model, prompt_id, context_length
    
    # Fallback for older pattern like results_dataset_1000.json
    match = re.search(r'results_([a-z]+)_(\d+)\.json', filename)
    if match:
        model = match.group(1)
        context_length = int(match.group(2))
        return model, None, context_length
    
    return None, None, None

def extract_sequence_similarity(file_path):
    """Extract the strict_sequence_similarity (Full) mean value from the result file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Extract the mean value from aggregate statistics
    return data['aggregate_statistics']['strict_sequence_similarity (Full)']['mean']

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Plot sequence similarity across different context lengths")
    parser.add_argument('--input_files', nargs='+', help='List of result JSON files to process')
    parser.add_argument('--output', help='Output path for the plot image')
    parser.add_argument('--model', help='Filter results by model (e.g., imagen, gemini)')
    args = parser.parse_args()
    
    # If input_files not provided, use default behavior
    if args.input_files is None:
        # Path to the result directory
        result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result')
        # Get all result files
        result_files = [f for f in os.listdir(result_dir) if f.endswith('.json')]
        # Create full paths
        file_paths = [os.path.join(result_dir, file) for file in result_files]
    else:
        # Use provided input files
        file_paths = args.input_files
    
    # Dictionary to store data grouped by model and prompt_id
    # Structure: {model: {prompt_id: [(context_length, sequence_similarity), ...], ...}, ...}
    grouped_data = {}
    
    # Extract data from files
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        model, prompt_id, context_length = extract_filename_info(file_name)
        
        # Skip if we couldn't extract necessary information
        if model is None or context_length is None:
            print(f"Skipping {file_name} - couldn't extract information")
            continue
            
        # Filter by model if specified
        if args.model and model != args.model:
            continue
            
        sequence_similarity = extract_sequence_similarity(file_path)
        
        # Initialize nested dictionaries if needed
        if model not in grouped_data:
            grouped_data[model] = {}
        if prompt_id not in grouped_data[model]:
            grouped_data[model][prompt_id] = []
            
        grouped_data[model][prompt_id].append((context_length, sequence_similarity))
    
    # Sort data in each group by context length
    for model in grouped_data:
        for prompt_id in grouped_data[model]:
            grouped_data[model][prompt_id].sort(key=lambda x: x[0])
    
    # Create a figure for each model
    for model in grouped_data:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Color map for different prompt IDs
        colors = plt.cm.tab10.colors
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        
        # Line chart for each prompt ID
        legend_handles = []
        for i, prompt_id in enumerate(sorted(grouped_data[model].keys())):
            data = grouped_data[model][prompt_id]
            context_lengths = [item[0] for item in data]
            sequence_similarities = [item[1] for item in data]
            
            color_idx = i % len(colors)
            marker_idx = i % len(markers)
            
            line, = ax.plot(context_lengths, sequence_similarities, 
                          marker=markers[marker_idx], linestyle='-', 
                          color=colors[color_idx], markersize=8,
                          label=f'Prompt ID {prompt_id}')
            legend_handles.append(line)
            
            # Add values as text labels on the chart
            for x, y in zip(context_lengths, sequence_similarities):
                ax.text(x, y + 0.002, f'{y:.4f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Context Length')
        ax.set_ylabel('Strict Sequence Similarity (Full)')
        ax.set_title(f'{model.capitalize()}: Strict Sequence Similarity vs Context Length')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend with dynamically created handles
        ax.legend(handles=legend_handles, loc='best')
        
        # Adjust layout and save figure
        plt.tight_layout()
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'result')
            output_path = os.path.join(result_dir, f'sequence_similarity_{model}.png')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save the figure
        plt.savefig(output_path)
        print(f"Plot for {model} saved to {output_path}")
        
    # Also display the data in the console
    print("\nData extracted:")
    print("Model | Prompt ID | Context Length | Strict Sequence Similarity (Full)")
    print("-" * 65)
    for model in grouped_data:
        for prompt_id in sorted(grouped_data[model].keys()):
            for length, similarity in grouped_data[model][prompt_id]:
                print(f"{model:10} | {prompt_id:10} | {length:14} | {similarity:.6f}")

if __name__ == "__main__":
    main()
