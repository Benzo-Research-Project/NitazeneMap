import os
import subprocess

SCRIPTS_FOLDER = "in_house_bi/scripts"

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

    # 1. Process the newest CSV
    run_script("process_month.py")

    # 2. Generate all plots
    run_script("generate_plots.py")

    # 3. Generate monthly summary text
    run_script("generate_summary.py")

    print("\n🎉 REFRESH COMPLETE!")
    print("All data, plots, and summaries are now up to date.\n")


if __name__ == "__main__":
    main()
``
