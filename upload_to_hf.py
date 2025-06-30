#!/usr/bin/env python3
"""
Script to upload experimental results to Hugging Face.
Uploads the /gemini directory to STRICT-Bench/strict repository.
"""

import os
import sys
import argparse
from pathlib import Path
from huggingface_hub import login, HfApi, create_repo
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Upload experiment results to Hugging Face")
    parser.add_argument(
        "--source-dir", 
        type=str, 
        default="experiment_results_20250629_231810_imagen/bbc_5000",
        help="Source directory containing the files to upload"
    )
    parser.add_argument(
        "--repo-id", 
        type=str, 
        default="STRICT-Bench/strict", 
        help="Target Hugging Face repository ID"
    )
    parser.add_argument(
        "--token", 
        type=str, 
        default=os.getenv("HUGGING_FACE_TOKEN"),
        help="Hugging Face API token. If not provided, will look for HUGGING_FACE_TOKEN env var"
    )
    parser.add_argument(
        "--create-repo", 
        action="store_true", 
        help="Create the repository if it doesn't exist"
    )
    parser.add_argument(
        "--path-in-repo", 
        type=str, 
        default="imagen/bbc",
        help="Path within the repo to store the files"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Check if source directory exists
    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} does not exist.")
        sys.exit(1)
        
    # Get token from args or environment
    token = args.token or os.environ.get("HUGGING_FACE_TOKEN")
    if not token:
        print("Error: Hugging Face token not provided. Use --token or set HUGGING_FACE_TOKEN env var.")
        sys.exit(1)
    
    # Login to Hugging Face
    print(f"Logging in to Hugging Face with provided token...")
    login(token=token, add_to_git_credential=True)
    
    # Initialize API
    api = HfApi()
    
    # Create repository if requested and doesn't exist
    if args.create_repo:
        try:
            print(f"Creating repository {args.repo_id} if it doesn't exist...")
            create_repo(repo_id=args.repo_id, token=token, exist_ok=True)
        except Exception as e:
            print(f"Error creating repository: {e}")
            sys.exit(1)
    
    # Upload directory contents
    print(f"Uploading files from {source_dir} to {args.repo_id}/{args.path_in_repo}...")
    api.upload_folder(
        folder_path=str(source_dir),
        repo_id=args.repo_id,
        repo_type="dataset",  # or "model" if appropriate
        path_in_repo=args.path_in_repo,
        commit_message=f"Upload {source_dir.name} directory",
    )
    
    print(f"Upload complete! Files are available at: https://huggingface.co/datasets/{args.repo_id}")


if __name__ == "__main__":
    main()
