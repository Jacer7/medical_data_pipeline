CREATE DATABASE dagster_backend;
CREATE DATABASE medical_data;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE medical_data TO pipeline_user;
GRANT ALL PRIVILEGES ON DATABASE dagster_backend TO pipeline_user;