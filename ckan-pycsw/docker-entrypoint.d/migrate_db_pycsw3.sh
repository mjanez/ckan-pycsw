#!/bin/bash
# pycsw 2.x to 3.0 Database Migration Script
# This script adds new model fields required by pycsw 3.0
# Reference: https://docs.pycsw.org/en/latest/migration-guide.html

set -e

echo "[pycsw migration] Starting database migration from pycsw 2.x to 3.0..."

# Use PYCSW_CONFIG from environment variable (should be set by Dockerfile)
CONFIG_FILE="${PYCSW_CONFIG}"

# Extract database URL from config using grep and sed (avoids Python dependency)
if [ -f "$CONFIG_FILE" ]; then
    # Extract database line from YAML config (format: "database: sqlite:///path/to/db")
    DB_URL=$(grep -E "^\s*database:\s*" "$CONFIG_FILE" | sed 's/.*database:\s*//' | tr -d '"' | tr -d "'")
    
    if [ -z "$DB_URL" ]; then
        echo "[ERROR] Could not extract database URL from config file"
        echo "[INFO] Skipping migration"
        exit 0
    fi
else
    echo "[ERROR] Config file not found: $CONFIG_FILE"
    echo "[INFO] Skipping migration - file will be created on first run"
    exit 0
fi

echo "[pycsw migration] Database URL: $DB_URL"

# Determine database type
if [[ $DB_URL == sqlite* ]]; then
    echo "[pycsw migration] Detected SQLite database"
    
    # Extract database path from sqlite:///path/to/db
    DB_PATH=$(echo $DB_URL | sed 's|sqlite:///||')
    
    if [ ! -f "$DB_PATH" ]; then
        echo "[WARNING] Database file does not exist yet: $DB_PATH"
        echo "[INFO] Migration will be skipped. Database will be created with new schema."
        exit 0
    fi
    
    # Run SQLite migration
    echo "[pycsw migration] Adding new fields to SQLite database..."
    sqlite3 "$DB_PATH" <<EOF
-- Check if columns already exist before adding them
PRAGMA table_info(records);

-- Add new columns for pycsw 3.0
ALTER TABLE records ADD COLUMN metadata TEXT;
ALTER TABLE records ADD COLUMN metadata_type TEXT DEFAULT 'application/xml';
ALTER TABLE records ADD COLUMN edition TEXT;
ALTER TABLE records ADD COLUMN contacts TEXT;
ALTER TABLE records ADD COLUMN themes TEXT;

-- Optimize database
VACUUM;
EOF
    
    echo "[pycsw migration] SQLite migration completed successfully"

elif [[ $DB_URL == postgresql* ]]; then
    echo "[pycsw migration] Detected PostgreSQL database"
    
    # Run PostgreSQL migration
    echo "[pycsw migration] Adding new fields to PostgreSQL database..."
    psql "$DB_URL" <<EOF
-- Add new columns for pycsw 3.0 (IF NOT EXISTS for safety)
DO \$\$
BEGIN
    -- metadata column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='records' AND column_name='metadata'
    ) THEN
        ALTER TABLE records ADD COLUMN metadata TEXT;
    END IF;
    
    -- metadata_type column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='records' AND column_name='metadata_type'
    ) THEN
        ALTER TABLE records ADD COLUMN metadata_type TEXT DEFAULT 'application/xml';
    END IF;
    
    -- edition column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='records' AND column_name='edition'
    ) THEN
        ALTER TABLE records ADD COLUMN edition TEXT;
    END IF;
    
    -- contacts column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='records' AND column_name='contacts'
    ) THEN
        ALTER TABLE records ADD COLUMN contacts TEXT;
    END IF;
    
    -- themes column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='records' AND column_name='themes'
    ) THEN
        ALTER TABLE records ADD COLUMN themes TEXT;
    END IF;
END
\$\$;

-- Vacuum analyze for optimization
VACUUM ANALYZE records;
EOF
    
    echo "[pycsw migration] PostgreSQL migration completed successfully"

elif [[ $DB_URL == mysql* ]]; then
    echo "[pycsw migration] Detected MySQL database"
    
    # Extract connection info from mysql://user:pass@host/db
    MYSQL_CONN=$(echo $DB_URL | sed 's|mysql://||' | sed 's|?.*||')
    
    # Run MySQL migration
    echo "[pycsw migration] Adding new fields to MySQL database..."
    mysql "$MYSQL_CONN" <<EOF
-- Add new columns for pycsw 3.0 (IF NOT EXISTS for safety)
ALTER TABLE records 
    ADD COLUMN IF NOT EXISTS metadata TEXT,
    ADD COLUMN IF NOT EXISTS metadata_type TEXT DEFAULT 'application/xml',
    ADD COLUMN IF NOT EXISTS edition TEXT,
    ADD COLUMN IF NOT EXISTS contacts TEXT,
    ADD COLUMN IF NOT EXISTS themes TEXT;

-- Optimize table
OPTIMIZE TABLE records;
EOF
    
    echo "[pycsw migration] MySQL migration completed successfully"

else
    echo "[WARNING] Unknown database type: $DB_URL"
    echo "[INFO] Migration script supports: sqlite, postgresql, mysql"
    echo "[INFO] Please run migration manually if needed"
    exit 1
fi

echo "[pycsw migration] Database migration completed successfully!"
echo "[INFO] New fields added: metadata, metadata_type, edition, contacts, themes"
