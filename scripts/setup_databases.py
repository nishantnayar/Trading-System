#!/usr/bin/env python3
"""
Database Setup Script for Trading System
Creates the Prefect database and sets up the environment configuration.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))


def run_sql_command(command: str, database: str = "postgres") -> bool:
    """Run a SQL command using psycopg2"""
    try:
        # Get database connection details from environment
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "")

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, database=database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        # Execute command
        cursor = conn.cursor()
        cursor.execute(command)
        cursor.close()
        conn.close()

        print(f"Successfully executed: {command}")
        return True

    except psycopg2.OperationalError as e:
        print(f"Database connection error: {e}")
        return False
    except Exception as e:
        print(f"Error running SQL command: {e}")
        return False


def create_prefect_database():
    """Create the Prefect database"""
    print("Creating Prefect database...")

    # Check if database already exists
    check_db_cmd = """
    SELECT 1 FROM pg_database WHERE datname = 'Prefect';
    """

    if run_sql_command(check_db_cmd, "trading_system"):
        print("Prefect database already exists")
        return True

    # Create the database
    create_db_cmd = 'CREATE DATABASE "Prefect";'
    if run_sql_command(create_db_cmd, "trading_system"):
        print("Prefect database created successfully")

        # Grant permissions
        grant_cmd = 'GRANT ALL PRIVILEGES ON DATABASE "Prefect" TO postgres;'
        if run_sql_command(grant_cmd, "trading_system"):
            print("Permissions granted to postgres user")
            return True

    return False


def create_service_schemas():
    """Create service-specific schemas in trading_system database"""
    print("\nCreating service-specific schemas...")

    schemas = [
        "data_ingestion",
        "strategy_engine",
        "execution",
        "risk_management",
        "analytics",
        "notification",
        "logging",
        "shared",
    ]

    for schema in schemas:
        create_schema_cmd = f"\nCREATE SCHEMA IF NOT EXISTS {schema};"
        if run_sql_command(create_schema_cmd, "trading_system"):
            print(f"Schema '{schema}' created/verified\n")
        else:
            print(f"Failed to create schema '{schema}'")
            return False

    return True


def setup_prefect_config():
    """Setup Prefect configuration"""
    print("\n\nSetting up Prefect configuration...")

    # Get database connection details
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")

    # Construct Prefect database URL
    prefect_db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/Prefect"

    try:
        # Set Prefect database URL
        subprocess.run(
            [
                "prefect",
                "config",
                "set",
                f"PREFECT_API_DATABASE_CONNECTION_URL={prefect_db_url}",
            ],
            check=True,
        )

        print("\nPrefect database URL configured")

        # Note: Prefect will automatically initialize its database tables when the server starts
        # No manual database upgrade command is needed in newer Prefect versions
        print(
            "\nPrefect database will be initialized automatically when server starts\n"
        )

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error setting up Prefect configuration: {e}")
        return False
    except FileNotFoundError:
        print("Prefect command not found. Please install Prefect first.")
        return False


def verify_databases():
    """Verify that both databases exist and are accessible"""

    print("=" * 50)
    print("Starting verifying database setup...")

    # Check trading_system database
    if run_sql_command("SELECT 1;", "trading_system"):
        print("trading_system database is accessible")
    else:
        print("trading_system database is not accessible")
        return False

    # Check prefect database
    if run_sql_command("SELECT 1;", "Prefect"):
        print("Prefect database is accessible")
    else:
        print("Prefect database is not accessible")
        return False

    return True


def main():
    """Main setup function"""
    print("=" * 50)
    print("\nStarting Database Setup for Trading System\n")
    print("=" * 50)

    # Check if required environment variables are set
    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False

    # Step 1: Create Prefect database
    if not create_prefect_database():
        print("Failed to create Prefect database")
        return False

    # Step 2: Create service schemas
    if not create_service_schemas():
        print("Failed to create service schemas")
        return False

    # Step 3: Setup Prefect configuration
    if not setup_prefect_config():
        print("Failed to setup Prefect configuration")
        return False

    # Step 4: Verify setup
    if not verify_databases():
        print("Database verification failed")
        return False

    print("=" * 50)
    print("\nDatabase setup completed successfully!\n")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
