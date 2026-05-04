import os
import subprocess


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_FOLDER = os.path.join(BASE_DIR)


def run_script(script_name):
    """Helper to run another script and show output."""
    path = os.path.join(SCRIPTS_FOLDER, script_name)
    print(f"\n▶️ Running {script_name} ...")
    
    result = subprocess.run(["python", path], capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("⚠️ ERRORS / WARNINGS:")
        print(result.stderr)


def main():
    print("\n🚀 REFRESH STARTED — Updating all outputs...\n")

    # STEP 1
    print("▶️ Step 1 — Processing data")
    run_script("process_month.py")

    # STEP 2
    print("\n▶️ Step 2 — Generating plots")
    run_script("generate_plots.py")

    # STEP 3
    print("\n▶️ Step 3 — Generating summary")
    run_script("generate_summary.py")

    print("\n🎉 REFRESH COMPLETE!")
    print("All data, plots, and summaries are now up to date.\n")


if __name__ == "__main__":
    main()

