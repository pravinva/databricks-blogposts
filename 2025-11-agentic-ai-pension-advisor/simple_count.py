#!/usr/bin/env python3
"""
Simple count query to verify data exists
"""

import os
os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo-west'

from databricks.sdk import WorkspaceClient

def simple_count():
    """Simple count query"""

    w = WorkspaceClient()

    catalog = "financial_services"
    schema = "pension_advisory"
    warehouse_id = "75fd8278393d07eb"

    query = f"SELECT COUNT(*) as count FROM {catalog}.{schema}.member_profiles"

    print(f"Executing: {query}")
    print(f"Warehouse: {warehouse_id}")
    print(f"Profile: {os.environ.get('DATABRICKS_CONFIG_PROFILE')}")
    print()

    try:
        result = w.statement_execution.execute_statement(
            statement=query,
            warehouse_id=warehouse_id,
            catalog=catalog,
            schema=schema
        )

        print(f"Status: {result.status}")
        print(f"Result: {result.result}")

        if result.result:
            print(f"Data array: {result.result.data_array}")
            if result.result.data_array:
                count = result.result.data_array[0][0]
                print(f"\nTotal rows in member_profiles: {count}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_count()
