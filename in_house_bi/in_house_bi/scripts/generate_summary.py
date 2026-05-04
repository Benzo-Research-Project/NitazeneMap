import pandas as pd
import os
from datetime import datetime


import os

BASE_DIR = os.path.dirname(__file__)

# Data locations
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
PROCESSED_FOLDER = os.path.join(DATA_DIR, "processed")

# Output location
SUMMARY_FOLDER = os.path.join(BASE_DIR, "..", "outputs", "summaries")

# Ensure output folder exists
os.makedirs(SUMMARY_FOLDER, exist_ok=True)


def load_latest_processed():
    files = [f for f in os.listdir(PROCESSED_FOLDER)
             if f.startswith("processed_") and f.endswith(".csv")]

    if not files:
        print("❌ No processed CSV files found.")
        return None, None

    latest = max(
        files,
        key=lambda x: os.path.getmtime(os.path.join(PROCESSED_FOLDER, x))
    )

    path = os.path.join(PROCESSED_FOLDER, latest)

    print(f"📄 Loaded processed dataset: {latest}")
    df = pd.read_csv(path)

    return df, latest



def write_summary(text, year_month):
    """Save text summary to summaries folder."""
    filename = f"{year_month}_summary.txt"
    path = os.path.join(SUMMARY_FOLDER, filename)

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"📝 Summary saved to: {path}")


def generate_summary(df, year_month):
    """Create a clear, understandable monthly drug summary."""

    month_name = pd.to_datetime(year_month).strftime("%B %Y")

    total_samples = len(df)

    # Top substances
    major_counts = df["major"].value_counts()
    top_sub = major_counts.idxmax()
    top_sub_count = major_counts.max()

    # Mixtures
    mixture_rate = df["is_mixture"].mean() * 100
    mixture_rate = round(mixture_rate, 1)

    # All substances appearing this month
    substances = sorted(set(df["major"].dropna().unique()))

    # Detect novel substances (never seen before)
    # Load all processed history
    history_files = [f for f in os.listdir(PROCESSED_FOLDER) if f.endswith(".csv")]
    dfs = [pd.read_csv(os.path.join(PROCESSED_FOLDER, f)) for f in history_files]
    history = pd.concat(dfs, ignore_index=True)

    prev_months = history[history["year_month"] != year_month]

    previous_subs = set(prev_months["major"].dropna().unique())
    new_substances = [s for s in substances if s not in previous_subs]

    # Summary text (clear, comms‑ready)
    summary = f"""
MONTHLY DRUG SUMMARY — {month_name}

Total samples analysed this month: {total_samples}

Most common benzodiazepine detected:
- {top_sub} ({top_sub_count} detections)

Mixture patterns:
- {mixture_rate}% of samples contained more than one substance, which increases risk.

Benzodiazepines detected this month:
- {", ".join(substances)}

New or unusual substances detected:
- {", ".join(new_substances) if new_substances else "None identified this month"}

Notes:
- This summary provides an overview of substances found in samples from wedinos.
- Results reflect only the samples submitted and may not represent the full drug supply.
    """

    return summary.strip()


def main():
    print("🚀 Generating summary text...")

    df = load_latest_processed()
    if df is None:
        return

    year_month = df["year_month"].iloc[0]

    text = generate_summary(df, year_month)
    write_summary(text, year_month)

    print("\n🎉 Summary generated successfully.")
    print("You can now copy/paste it into Canva or comms materials.")


if __name__ == "__main__":
    main()
