#!/usr/bin/env python3
"""
Script to run the medical data pipeline
"""

from dagster import DagsterInstance
from dagster_project import defs

def run_validated_pipeline():
    """Run the validated CSV to PostgreSQL pipeline"""

    # Get the job
    job = defs.get_job_def("validated_csv_to_postgres_pipeline")

    # Create instance
    instance = DagsterInstance.ephemeral()

    # Execute the job
    result = job.execute_in_process(instance=instance)

    if result.success:
        print("Pipeline executed successfully!")
        print(f"Run ID: {result.run_id}")
    else:
        print("Pipeline failed!")
        for event in result.all_events:
            if event.is_failure:
                print(f"Error: {event}")

    return result

def run_simple_pipeline():
    """Run the simple CSV to PostgreSQL pipeline"""

    job = defs.get_job_def("csv_to_postgres_pipeline")
    instance = DagsterInstance.ephemeral()
    result = job.execute_in_process(instance=instance)

    if result.success:
        print("Simple pipeline executed successfully!")
    else:
        print("Simple pipeline failed!")

    return result

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "simple":
        run_simple_pipeline()
    else:
        run_validated_pipeline()