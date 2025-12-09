#!/usr/bin/env python3
"""
Check the actual table: financial_services.pension_advisory.member_profiles
"""

import os
os.environ['DATABRICKS_CONFIG_PROFILE'] = 'e2-demo-west'

from databricks.sdk import WorkspaceClient

def check_actual_table():
    """Query the actual production table"""

    w = WorkspaceClient()

    # Hardcode the actual table location
    catalog = "financial_services"
    schema = "pension_advisory"
    warehouse_id = "75fd8278393d07eb"

    query = f"""
    SELECT
        member_id,
        name,
        age,
        pension_balance,
        pension_type,
        country
    FROM {catalog}.{schema}.member_profiles
    ORDER BY country, member_id
    LIMIT 20
    """

    print("=" * 80)
    print(f"Querying: {catalog}.{schema}.member_profiles")
    print("=" * 80)

    try:
        result = w.statement_execution.execute_statement(
            statement=query,
            warehouse_id=warehouse_id,
            catalog=catalog,
            schema=schema
        )

        if result.result and result.result.data_array:
            print(f"\nFound {len(result.result.data_array)} members:")
            print("-" * 80)
            for row in result.result.data_array:
                member_id, name, age, balance, pension_type, country = row
                print(f"{member_id:10} | {name:25} | Age {age:2} | {balance:12.2f} | {pension_type:15} | {country}")

            # Now show just UK members
            query_uk = f"""
            SELECT
                member_id,
                name,
                age,
                pension_balance,
                pension_type,
                country
            FROM {catalog}.{schema}.member_profiles
            WHERE country = 'UK'
            ORDER BY member_id
            """

            result_uk = w.statement_execution.execute_statement(
                statement=query_uk,
                warehouse_id=warehouse_id,
                catalog=catalog,
                schema=schema
            )

            print("\n" + "=" * 80)
            print("UK Members with Pension Types:")
            print("=" * 80)

            if result_uk.result and result_uk.result.data_array:
                for row in result_uk.result.data_array:
                    member_id, name, age, balance, pension_type, country = row
                    print(f"\n{member_id}: {name}")
                    print(f"  Age: {age}")
                    print(f"  Balance: {balance:.2f} GBP")
                    print(f"  Pension Type: {pension_type}")
            else:
                print("No UK members found")

        else:
            print("No data found in table")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_actual_table()
