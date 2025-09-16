from dagster import op, job, OpExecutionContext
from storage.medical_database import create_medical_tables

@op
def create_database_tables_op(context: OpExecutionContext):
    """Operation to create medical database tables"""
    create_medical_tables()
    context.log.info("Database tables setup completed")
    return "Medical database tables created successfully"

@job(name="setup_medical_database")
def setup_medical_database_job():
    """One-time setup job for creating database tables"""
    create_database_tables_op()