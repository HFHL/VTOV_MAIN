from huggingface_hub import snapshot_download
import os

repo_id = "STRICT-Bench/strict"  # Replace with the actual Gemini/Gemma repo ID
local_dir = "results_all"  # Adjust the path as needed

# Create the local directory if it doesn't exist
os.makedirs(local_dir, exist_ok=True)

# allow_patterns = ["anytext2/*", "flux/*", "flux_batch2/*", "recraft/*", "recraft_batch2/*", "seedream/*", "seedream_batch2/*", "textdiffuser2/*"]
allow_patterns = ["gpt/*", "gpt_batch2/*", "hidream/*", "hidream_batch2/*"]

try:
    snapshot_download(repo_id=repo_id, local_dir=local_dir, repo_type="dataset", allow_patterns=allow_patterns)
    print(f"Successfully downloaded {repo_id} to {local_dir}")
except Exception as e:
    print(f"Error downloading {repo_id}: {e}")
