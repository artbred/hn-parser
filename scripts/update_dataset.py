import os
import subprocess
import pandas as pd
from datasets import load_dataset, Dataset
from huggingface_hub import login

# Configuration
DATASET_REPO = "artbred/hn_stories"
OUTPUT_FILE = "new_stories.jsonl"
GO_BINARY = "./hn_parser"

def main():
    # 1. Login to Hugging Face
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable is not set")
    login(token=hf_token)
    print("Logged in to Hugging Face")

    # 2. Load existing dataset to find the last ID
    print(f"Loading dataset {DATASET_REPO}...")
    min_score = 10
    last_id = 0
    ds = None

    cmd = [
        GO_BINARY,
        "-output", OUTPUT_FILE,
        "-min-score", str(min_score),
        "-stories", "50000"
    ]
    
    try:
        ds = load_dataset(DATASET_REPO, split="train")
        if len(ds) > 0:
            # Assuming 'id' column exists
            last_id = max(ds['id'])
            print(f"Found existing dataset with {len(ds)} stories. Last ID: {last_id}")
            cmd = [
                GO_BINARY,
                "-output", OUTPUT_FILE,
                "-stop-at-id", str(last_id),
                "-min-score", str(min_score),
                "-stories", "0"
            ]
        else:
            print("Dataset is empty. Starting from scratch.")

    except Exception as e:
        print(f"Error loading dataset (might be first run or dataset doesn't exist): {e}")
        pass

    # 3. Run Go parser to fetch new stories
    print(f"Running HN parser stopping at ID {last_id}...")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Go parser: {e}")
        # Proceed only if output file exists
        if not os.path.exists(OUTPUT_FILE):
             raise

    # 4. Process new stories
    if not os.path.exists(OUTPUT_FILE):
        print("No output file generated. Maybe no new stories?")
        return

    # Check if file is empty
    if os.path.getsize(OUTPUT_FILE) == 0:
        print("Output file is empty. No new stories found.")
        return

    print(f"Reading new stories from {OUTPUT_FILE}...")
    try:
        new_df = pd.read_json(OUTPUT_FILE, lines=True)
        print(f"Fetched {len(new_df)} new stories.")
    except ValueError:
         print("Could not read JSONL file. It might be empty or invalid.")
         return

    if len(new_df) == 0:
        print("No new stories to update.")
        return

    # 5. Merge with existing dataset
    if ds is not None:
        print("Merging with existing dataset...")
        existing_df = ds.to_pandas()
        
        # Ensure columns match - add missing columns to new_df if necessary
        # (Go parser might output consistent JSON, but safe to check)
        
        # Concatenate
        combined_df = pd.concat([existing_df, new_df])
        
        # Deduplicate by ID, keeping the new version (from new_df which is at the end usually, but let's be safe)
        # We want to keep the LATEST fetched version if there's an update, though IDs are immutable on HN usually.
        combined_df = combined_df.drop_duplicates(subset=['id'], keep='last')
        
        # Sort by ID descending (newest first)
        combined_df = combined_df.sort_values('id', ascending=False)
    else:
        combined_df = new_df
        combined_df = combined_df.sort_values('id', ascending=False)

    print(f"Total stories after merge: {len(combined_df)}")

    # 6. Upload updated dataset
    print("Pushing to Hugging Face...")
    combined_df = combined_df.reset_index(drop=True)
    
    if "__index_level_0__" in combined_df.columns:
        combined_df = combined_df.drop(columns=["__index_level_0__"])

    new_ds = Dataset.from_pandas(combined_df)
    # Push to 'train' split
    new_ds.push_to_hub(DATASET_REPO, token=hf_token)
    print("Successfully updated dataset!")

if __name__ == "__main__":
    main()

