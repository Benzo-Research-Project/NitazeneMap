import pandas as pd
import os
from datetime import datetime

# -----------------------
# Folder configuration
# -----------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")

RAW_DATA_FOLDER = os.path.join(DATA_DIR, "raw")
PROCESSED_FOLDER = os.path.join(DATA_DIR, "processed")
def select_csv():
    """Let user choose a CSV from the raw folder."""

    files = [f for f in os.listdir(RAW_DATA_FOLDER) if f.lower().endswith(".csv")]

    if not files:
        print("❌ No CSV files in raw folder.")
        return None, None

    print("\n📂 Available files:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")

    choice = input("\nEnter the number of the file to use: ")

    try:
        index = int(choice) - 1
        selected = files[index]
    except:
        print("❌ Invalid selection.")
        return None, None

    path = os.path.join(RAW_DATA_FOLDER, selected)

    print(f"\n📄 Loading CSV: {selected}")
    df = pd.read_csv(path)

    return df, selected


def clean_dataframe(df):
    """Clean Wedinos dataframe and standardise column names."""

    # Fix first unnamed column (sample IDs)
    if df.columns[0] == "" or df.columns[0].startswith("Unnamed"):
        df = df.rename(columns={df.columns[0]: "sample_id"})

    # Standardise remaining column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Parse dates
    df["date_received"] = pd.to_datetime(df["date_received"], format="%d %b %Y", errors="coerce")

    # Create year-month column (for grouping)
    df["year_month"] = df["date_received"].dt.to_period("M").astype(str)

    # Clean major/minor substance fields
    df["major"] = df["major"].astype(str).str.strip()
    df["minor"] = df["minor"].astype(str).str.strip()

    # Identify mixtures
    df["is_mixture"] = df["minor"].apply(lambda x: False if x in ["", "nan", "None"] else True)

    return df


def count_substances(df):
    """Count detected substances (major and minor)."""

    # Count major substances
    major_counts = df["major"].value_counts().reset_index()
    major_counts.columns = ["substance", "count_major"]

    # Count minor substances
    minor_only = df[df["minor"].notna() & (df["minor"] != "")]
    minor_counts = minor_only["minor"].value_counts().reset_index()
    minor_counts.columns = ["substance", "count_minor"]

    # Merge both
    substance_counts = pd.merge(major_counts, minor_counts, on="substance", how="outer").fillna(0)

    # Total frequency
    substance_counts["total_count"] = (
        substance_counts["count_major"] + substance_counts["count_minor"]
    ).astype(int)

    # Sort
    substance_counts = substance_counts.sort_values("total_count", ascending=False)

    return substance_counts


def save_processed(df, filename):
    """Save cleaned dataframe into processed folder."""
    cleaned_name = f"processed_{filename}"
    path = os.path.join(PROCESSED_FOLDER, cleaned_name)
    df.to_csv(path, index=False)
    print(f"💾 Saved cleaned CSV → {path}")


def main():
    print("🚀 Running monthly processing...")

   import sys

file_arg = sys.argv[1] if len(sys.argv) > 1 else None

df, filename = select_csv()
    if df is None:
        return

    df = clean_dataframe(df)
    save_processed(df, filename)

    substance_counts = count_substances(df)

    print("\n📊 Top detected substances this month:")
    print(substance_counts.head(10))

    print("\n🎉 Step 4 complete — data cleaned and substance frequencies generated.")


if __name__ == "__main__":
    main()
