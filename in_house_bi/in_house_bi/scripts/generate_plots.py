import pandas as pd
import matplotlib.pyplot as plt
import os



BASE_DIR = os.path.dirname(__file__)

DATA_DIR = os.path.join(BASE_DIR, "..", "data")
PROCESSED_FOLDER = os.path.join(DATA_DIR, "processed")

PLOTS_FOLDER = os.path.join(BASE_DIR, "..", "outputs", "plots")

os.makedirs(PLOTS_FOLDER, exist_ok=True)




def load_latest_processed():
    """Load the most recently cleaned monthly dataset."""
    files = [f for f in os.listdir(PROCESSED_FOLDER) if f.startswith("processed_") and f.endswith(".csv")]

    if not files:
        print("❌ No processed CSV files found.")
        return None, None

        # pick the most recent one alphabetically
    latest = sorted(files)[-1]
    path = os.path.join(PROCESSED_FOLDER, latest)

    print(f"📄 Loading processed CSV: {latest}")
    df = pd.read_csv(path)

    # Extract month name for file naming
    year_month = df["year_month"].iloc[0]

    return df, year_month


def create_horizontal_bar_chart(substance_counts, year_month):
    """Generate a horizontal bar chart of top detected substances."""
    plt.figure(figsize=(10, 6))

    top10 = substance_counts.head(10)
    plt.barh(top10["substance"], top10["total_count"], color="#4C72B0")
    plt.xlabel("Detections")
    plt.ylabel("Substance")
    plt.title(f"Top Detected Benzodiazepines — {year_month}")
    plt.gca().invert_yaxis()  # most frequent at top

    filename = f"{year_month}_top_substances.png"
    filepath = os.path.join(PLOTS_FOLDER, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()

    print(f"📊 Saved horizontal bar chart → {filepath}")


def create_trend_line(all_data):
    """Create a multi-month trend line for the top substances."""
    # Melt major/minor into long format
    majors = all_data[["year_month", "major"]].rename(columns={"major": "substance"})
    minors = all_data[["year_month", "minor"]].rename(columns={"minor": "substance"})
    melted = pd.concat([majors, minors], ignore_index=True)

    melted = melted[melted["substance"].notna() & (melted["substance"] != "")]

    trend = (
        melted.groupby(["year_month", "substance"])
        .size()
        .reset_index(name="count")
    )

    # Top 5 substances overall
    top5_substances = (
        trend.groupby("substance")["count"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
        .index
    )

    trend_top5 = trend[trend["substance"].isin(top5_substances)]

    plt.figure(figsize=(12, 6))

    for substance in top5_substances:
        subset = trend_top5[trend_top5["substance"] == substance]
        plt.plot(subset["year_month"], subset["count"], marker="o", label=substance)

    plt.xlabel("Month")
    plt.ylabel("Detections")
    plt.title("Top Benzodiazepine Trends Over Time")
    plt.xticks(rotation=45)
    plt.legend()

    filename = "trend_top5_substances.png"
    filepath = os.path.join(PLOTS_FOLDER, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()

    print(f"📈 Saved trend line chart → {filepath}")


def main():
    print("🚀 Generating monthly visualisations...")

    df, year_month = load_latest_processed()
    if df is None:
        return

    # Compute substance counts
    major_counts = df["major"].value_counts().reset_index()
    major_counts.columns = ["substance", "count_major"]

    minors = df[df["minor"].notna() & (df["minor"] != "")]
    minor_counts = minors["minor"].value_counts().reset_index()
    minor_counts.columns = ["substance", "count_minor"]

    substance_counts = pd.merge(
        major_counts, minor_counts, on="substance", how="outer"
    ).fillna(0)

    substance_counts["total_count"] = (
        substance_counts["count_major"] + substance_counts["count_minor"]
    ).astype(int)

    substance_counts = substance_counts.sort_values("total_count", ascending=False)

    # Create visuals
    create_horizontal_bar_chart(substance_counts, year_month)

    # For trend over time, load all processed files
    all_files = [f for f in os.listdir(PROCESSED_FOLDER) if f.endswith(".csv")]
    dfs = [pd.read_csv(os.path.join(PROCESSED_FOLDER, f)) for f in all_files]
    all_data = pd.concat(dfs, ignore_index=True)

    create_trend_line(all_data)

    print("🎉 Step 5 complete — visualisations created.")


if __name__ == "__main__":
    main()
