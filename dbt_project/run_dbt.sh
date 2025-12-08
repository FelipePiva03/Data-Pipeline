#!/bin/bash
# Helper script to run dbt commands

# Load environment variables
export $(cat ../.env | grep -v '^#' | xargs)

# Set dbt profiles directory to current directory
export DBT_PROFILES_DIR=$(pwd)

# Execute dbt command
case "$1" in
    "run")
        dbt run --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        ;;
    "test")
        dbt test --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        ;;
    "debug")
        dbt debug --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        ;;
    "docs")
        dbt docs generate --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        dbt docs serve --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        ;;
    "silver")
        dbt run --select silver --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        ;;
    "gold")
        dbt run --select gold --profiles-dir $DBT_PROFILES_DIR --project-dir $DBT_PROFILES_DIR
        ;;
    *)
        echo "Usage: ./run_dbt.sh {run|test|debug|docs|silver|gold}"
        echo ""
        echo "Commands:"
        echo "  run    - Execute all dbt models"
        echo "  test   - Run all dbt tests"
        echo "  debug  - Test database connection"
        echo "  docs   - Generate and serve documentation"
        echo "  silver - Run only silver layer models"
        echo "  gold   - Run only gold layer models"
        exit 1
        ;;
esac
