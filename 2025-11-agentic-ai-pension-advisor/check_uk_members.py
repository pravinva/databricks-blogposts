#!/usr/bin/env python3
"""
Check UK member profiles and their pension types
"""

import os
from databricks.sdk import WorkspaceClient
from src.config import SQL_WAREHOUSE_ID, UNITY_CATALOG, UNITY_SCHEMA, MEMBER_PROFILES_TABLE

def check_uk_members():
    """Query UK members and show their pension types"""

    w = WorkspaceClient()

    # First, check all members
    query_all = f"""
    SELECT
        member_id,
        name,
        age,
        pension_balance,
        pension_type,
        country
    FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.{MEMBER_PROFILES_TABLE}
    ORDER BY country, member_id
    LIMIT 20
    """

    print("All Members (first 20):")
    print("=" * 80)

    result = w.statement_execution.execute_statement(
        statement=query_all,
        warehouse_id=SQL_WAREHOUSE_ID,
        catalog=UNITY_CATALOG,
        schema=UNITY_SCHEMA
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            member_id, name, age, balance, pension_type, country = row
            print(f"{member_id:10} | {name:20} | Age {age:2} | {balance:12.2f} | {pension_type:15} | {country}")

    print("\n")

    query = f"""
    SELECT
        member_id,
        name,
        age,
        pension_balance,
        pension_type,
        country
    FROM {UNITY_CATALOG}.{UNITY_SCHEMA}.{MEMBER_PROFILES_TABLE}
    WHERE country = 'UK'
    ORDER BY member_id
    """

    print("=" * 80)
    print("UK Member Profiles")
    print("=" * 80)

    result = w.statement_execution.execute_statement(
        statement=query,
        warehouse_id=SQL_WAREHOUSE_ID,
        catalog=UNITY_CATALOG,
        schema=UNITY_SCHEMA
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            member_id, name, age, balance, pension_type, country = row
            print(f"\nMember ID: {member_id}")
            print(f"Name: {name}")
            print(f"Age: {age}")
            print(f"Balance: {balance} GBP")
            print(f"Pension Type: {pension_type}")
            print("-" * 80)
    else:
        print("No UK members found")

if __name__ == "__main__":
    os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo-west'
    check_uk_members()
