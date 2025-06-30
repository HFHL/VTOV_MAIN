#!/usr/bin/env python3
import os
import json
import re
import argparse
import matplotlib.pyplot as plt
import numpy as np

def extract_filename_info(filename):
    """Extract model and context length from the filename."""
    # Match patterns like results_imagen_1000.json
    match = re.search(r'results_([a-z]+)_(\d+)\.json', filename)
    if match:
        model = match.group(1)
        context_length = int(match.group(2))
        return model, context_length
    
    return None, None

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

    print(args.input_files)
    
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
    
    # Dictionary to store data grouped by model and context_length
    # Structure: {model: {context_length: [sequence_similarity, ...], ...}, ...}
    grouped_data = {}
    
    # Extract data from files
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        model, context_length = extract_filename_info(file_name)
        
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
            
        grouped_data[model][context_length] = sequence_similarity
    
    # Create a figure for each model
    for model in grouped_data:
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Color map for different context lengths
        colors = plt.cm.tab10.colors
        markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
        
        # Plot data points for context lengths
        x_values = []
        y_values = []
        
        # Sort context lengths for proper plotting order
        context_lengths = sorted(grouped_data[model].keys())
        
        for context_length in context_lengths:
            similarity = grouped_data[model][context_length]
            x_values.append(context_length)
            y_values.append(similarity)
        
        # Plot the line
        line, = ax.plot(x_values, y_values, 
                      marker='o', linestyle='-', 
                      color=colors[0], markersize=8,
                      label=model.capitalize())
        
        # Add values as text labels on the chart
        for x, y in zip(x_values, y_values):
            ax.text(x, y + 0.002, f'{y:.4f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Context Length')
        ax.set_ylabel('Strict Sequence Similarity (Full)')
        ax.set_title(f'{model.capitalize()}: Strict Sequence Similarity vs Context Length')
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend
        ax.legend(loc='best')
        
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
    print("Model | Context Length | Strict Sequence Similarity (Full)")
    print("-" * 65)
    for model in grouped_data:
        for context_length in sorted(grouped_data[model].keys()):
            print(f"{model:10} | {context_length:14} | {grouped_data[model][context_length]:.6f}")

if __name__ == "__main__":
    main()
