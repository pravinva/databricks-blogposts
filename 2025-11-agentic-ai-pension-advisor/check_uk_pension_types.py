#!/usr/bin/env python3
"""
Check UK members and their actual pension configuration
"""

from databricks.sdk import WorkspaceClient

def check_uk_members():
    """Query UK members with all relevant columns"""

    w = WorkspaceClient()

    catalog = "financial_services"
    schema = "pension_advisory"
    warehouse_id = "4b9b953939869799"

    # First check what columns exist
    query_describe = f"DESCRIBE {catalog}.{schema}.member_profiles"

    print("=" * 80)
    print("Table Schema:")
    print("=" * 80)

    result = w.statement_execution.execute_statement(
        statement=query_describe,
        warehouse_id=warehouse_id,
        catalog=catalog,
        schema=schema
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            col_name = row[0]
            col_type = row[1]
            print(f"{col_name:30} {col_type}")

    print("\n" + "=" * 80)
    print("UK Members:")
    print("=" * 80)

    # Query UK members with pension-related fields
    query = f"""
    SELECT
        member_id,
        name,
        age,
        super_balance as pension_balance,
        account_based_pension,
        employment_status,
        country
    FROM {catalog}.{schema}.member_profiles
    WHERE country = 'UK'
    ORDER BY member_id
    """

    result = w.statement_execution.execute_statement(
        statement=query,
        warehouse_id=warehouse_id,
        catalog=catalog,
        schema=schema
    )

    if result.result and result.result.data_array:
        for row in result.result.data_array:
            member_id, name, age, balance, abp, emp_status, country = row
            print(f"\n{member_id}: {name}")
            print(f"  Age: {age}")
            print(f"  Balance: {balance} GBP")
            print(f"  Account Based Pension: {abp}")
            print(f"  Employment: {emp_status}")
    else:
        print("No UK members found")

if __name__ == "__main__":
    check_uk_members()
