from dagster import asset, job, op, OpExecutionContext
from storage.medical_database import create_medical_tables

@op
def setup_medical_database_op(context: OpExecutionContext):
    """One-time database setup operation"""
    create_medical_tables()
    context.log.info("Medical database tables created")
    return "Database setup complete"

@job
def setup_medical_database_job():
    """One-time job to set up database schema"""
    setup_medical_database_op()