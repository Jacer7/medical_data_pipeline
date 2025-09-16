# PostgreSQL Commands Reference

## Basic psql Navigation Commands

### Connecting to PostgreSQL

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U pipeline_user -d medical_pipeline

# Once connected, use these commands:
```

## Database Level Commands

```sql
\l          -- List all databases
\c dbname   -- Connect to a different database
\q          -- Quit psql
```

## Table Level Commands

```sql
\dt         -- List all tables in current database
\d          -- List all relations (tables, views, sequences)
\d+ tablename -- Describe table structure with details
\dt+        -- List tables with size information
```

## Schema and Structure Commands

```sql
\dn         -- List schemas
\df         -- List functions
\dv         -- List views
\di         -- List indexes
```

## Table Content Commands

```sql
SELECT * FROM tablename LIMIT 5;              -- View first 5 rows
SELECT COUNT(*) FROM tablename;               -- Count rows
\copy tablename TO '/tmp/export.csv' CSV HEADER;  -- Export to CSV
```

## Quick Database Exploration

```bash
# Connect and explore your current setup
docker-compose exec postgres psql -U pipeline_user -d medical_pipeline

# Then run these commands inside psql:
\dt                    # See what tables exist
\d+ publications      # See structure of publications table (if exists)
SELECT version();     # Confirm PostgreSQL version
SELECT current_database(); # Confirm current database
```

## Useful Queries

```sql
-- See all table names and row counts
SELECT 
    schemaname,
    tablename,
    n_tup_ins as "rows"
FROM pg_stat_user_tables;

-- Check table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(tablename::regclass)) as size
FROM pg_tables 
WHERE schemaname = 'public';
```