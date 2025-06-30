#!/usr/bin/env python3
"""
Script to upload a single file to Hugging Face.
Simplified version of upload_to_hf.py that handles a single file instead of a directory.
"""

import os
import sys
import argparse
from pathlib import Path
from huggingface_hub import login, HfApi, create_repo
from dotenv import load_dotenv

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description="Upload a single file to Hugging Face")
    parser.add_argument(
        "--file", 
        type=str, 
        default="/Users/fchi/Code/toy/VTOV_MAIN/gemini_imagen_results copy/en/evaluation_results.json",
        help="Path to the file to upload"
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
        default="gemini_batch2/en",
        help="Path within the repo to store the file. If not provided, will use the filename"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Check if source file exists
    file_path = Path(args.file)
    if not file_path.exists() or not file_path.is_file():
        print(f"Error: File {file_path} does not exist or is not a file.")
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
    
    # Determine path in repo
    path_in_repo = args.path_in_repo if args.path_in_repo else file_path.name
    
    # Upload file
    print(f"Uploading file {file_path} to {args.repo_id}/{path_in_repo}...")
    api.upload_file(
        path_or_fileobj=str(file_path),
        repo_id=args.repo_id,
        repo_type="dataset",
        path_in_repo=path_in_repo,
        commit_message=f"Upload {file_path.name}",
    )
    
    print(f"Upload complete! File is available at: https://huggingface.co/datasets/{args.repo_id}/blob/main/{path_in_repo}")


if __name__ == "__main__":
    main()
