-- Create databases (ignore errors if they exist)
CREATE DATABASE dagster_backend;
CREATE DATABASE medical_data;

-- Grant permissions (will succeed even if databases existed)
GRANT ALL PRIVILEGES ON DATABASE medical_data TO pipeline_user;
GRANT ALL PRIVILEGES ON DATABASE dagster_backend TO pipeline_user;