
import pandas as pd
import os

# --- CONFIGURATION ---
RAW_DATA_FOLDER = "in_house_bi/data/raw"
PROCESSED_FOLDER = "in_house_bi/data/processed"

def list_csv_files():
    """List all CSV files in the raw data folder."""
    files = [f for f in os.listdir(RAW_DATA_FOLDER) if f.lower().endswith(".csv")]
    return files

def load_latest_csv():
    """Load the most recent CSV file from the raw data folder."""
    files = list_csv_files()
    if not files:
        print("❌ No CSV files found in raw data folder.")
        return None

    latest = sorted(files)[-1]  # pick last alphabetically (date-based filenames will work)
    path = os.path.join(RAW_DATA_FOLDER, latest)

    print(f"📄 Loading CSV: {latest}")
    df = pd.read_csv(path)
    return df, latest

def main():
    print("🚀 Running process_month.py...")

    df, filename = load_latest_csv()
    if df is None:
        return

    print(f"✅ CSV Loaded Successfully: {filename}")
    print(f"📊 Rows: {len(df)} | Columns: {len(df.columns)}")

    # Save a processed copy (for now, identical)
    processed_path = os.path.join(PROCESSED_FOLDER, f"processed_{filename}")
    df.to_csv(processed_path, index=False)
    print(f"💾 Saved processed file to: {processed_path}")

    print("🎉 Step 3 successful: Basic script is working!")

if __name__ == "__main__":
    main()

