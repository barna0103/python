"""Check that your setup works by running every example in the course.

    python check_setup.py

Takes a few seconds. Everything runs offline: the LLM examples are
forced to use the built-in mock, so this never costs anything.
"""

import os
import subprocess
import sys
import time
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGES = ["pandas", "matplotlib", "requests", "anthropic"]

SCRIPTS = [
    "day1_python_foundations/01_reading_python.py",
    "day1_python_foundations/02_ticket_counts.py",
    "day1_python_foundations/03_sla_breaches.py",
    "day1_python_foundations/exercise.py",
    "day1_python_foundations/solutions/exercise_solution.py",
    "day2_sql/01_build_database.py",
    "day2_sql/02_sql_basics.py",
    "day2_sql/03_weekly_sla_report.py",
    "day2_sql/exercise.py",
    "day2_sql/solutions/exercise_solution.py",
    "day3_data_analysis/01_explore_tickets.py",
    "day3_data_analysis/02_support_metrics.py",
    "day3_data_analysis/03_product_funnel.py",
    "day3_data_analysis/exercise.py",
    "day3_data_analysis/solutions/exercise_solution.py",
    "day4_apis_logs_automation/01_call_an_api.py",
    "day4_apis_logs_automation/02_log_analysis.py",
    "day4_apis_logs_automation/03_escalation_report.py",
    "day4_apis_logs_automation/exercise.py",
    "day4_apis_logs_automation/solutions/exercise_solution.py",
    "day5_llm_agents/01_classify_tickets.py",
    "day5_llm_agents/02_agent_with_tools.py",
    "day5_llm_agents/03_weekly_report_pipeline.py",
    "day5_llm_agents/exercise.py",
    "day5_llm_agents/solutions/exercise_solution.py",
]


def main():
    print(f"Python {sys.version.split()[0]} at {sys.executable}")
    if sys.version_info < (3, 11):
        print("  PROBLEM: this course needs Python 3.11 or newer.")
        return 1

    missing = []
    for package in PACKAGES:
        try:
            print(f"  {package:<11} {metadata.version(package)}")
        except metadata.PackageNotFoundError:
            print(f"  {package:<11} NOT INSTALLED")
            missing.append(package)
    if missing:
        print("\nSome packages are missing. Days 1 and 2 will still work.")
        print("To fix: activate your virtual environment, then  pip install -r requirements.txt")

    environment = {**os.environ, "LLM_MODE": "mock"}
    failures = []
    print(f"\nRunning {len(SCRIPTS)} scripts ...")
    for script in SCRIPTS:
        started = time.time()
        result = subprocess.run([sys.executable, str(ROOT / script)], env=environment,
                                capture_output=True, text=True)
        seconds = time.time() - started
        verdict = "ok  " if result.returncode == 0 else "FAIL"
        print(f"  {verdict} {script}  ({seconds:.1f}s)")
        if result.returncode != 0:
            failures.append((script, result.stderr.strip().splitlines()[-1:] or ["no error text"]))

    if failures:
        print(f"\n{len(failures)} of {len(SCRIPTS)} scripts failed:")
        for script, last_line in failures:
            print(f"  {script}: {last_line[0]}")
        return 1

    print(f"\nAll {len(SCRIPTS)} scripts ran. You are ready for Day 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
