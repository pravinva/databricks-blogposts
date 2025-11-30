#!/usr/bin/env python3
"""
Check if governance table exists and see recent records
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from databricks.sdk import WorkspaceClient
from src.config import SQL_WAREHOUSE_ID, get_governance_table_path

def check_governance_table():
    """Check governance table status"""
    print("=" * 70)
    print("🔍 Checking Governance Table Status")
    print("=" * 70)

    w = WorkspaceClient()
    governance_table = get_governance_table_path()

    print(f"\n📊 Governance Table: {governance_table}")
    print(f"🔧 SQL Warehouse: {SQL_WAREHOUSE_ID}")

    # First, check if table exists
    print("\n🔄 Test 1: Check if table exists...")
    query1 = f"DESCRIBE TABLE {governance_table}"

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query1,
            wait_timeout="30s"
        )
        print("✅ Table exists!")

        if result.result and result.result.data_array:
            print(f"\n📋 Table Schema ({len(result.result.data_array)} columns):")
            for row in result.result.data_array[:10]:
                print(f"   - {row[0]}: {row[1]}")

    except Exception as e:
        print(f"❌ Table does not exist or cannot be accessed: {e}")
        return False

    # Check row count
    print("\n🔄 Test 2: Count total rows...")
    query2 = f"SELECT COUNT(*) FROM {governance_table}"

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query2,
            wait_timeout="30s"
        )

        if result.result and result.result.data_array:
            row_count = result.result.data_array[0][0]
            print(f"✅ Total rows: {row_count}")
        else:
            print("⚠️  Could not get row count")

    except Exception as e:
        print(f"❌ Error counting rows: {e}")

    # Get most recent 5 records
    print("\n🔄 Test 3: Get last 5 records...")
    query3 = f"""
    SELECT
        session_id,
        user_id,
        country,
        cost,
        timestamp
    FROM {governance_table}
    ORDER BY timestamp DESC
    LIMIT 5
    """

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query3,
            wait_timeout="30s"
        )

        if result.result and result.result.data_array:
            print(f"✅ Last 5 records:")
            for i, row in enumerate(result.result.data_array, 1):
                print(f"   {i}. User: {row[1]}, Country: {row[2]}, Cost: ${float(row[3]):.6f}, Time: {row[4]}")
        else:
            print("⚠️  No records found")

    except Exception as e:
        print(f"❌ Error getting records: {e}")

    # Check for IN003 records (any time)
    print("\n🔄 Test 4: Check for ANY IN003 records...")
    query4 = f"""
    SELECT COUNT(*) FROM {governance_table}
    WHERE user_id = 'IN003'
    """

    try:
        result = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query4,
            wait_timeout="30s"
        )

        if result.result and result.result.data_array:
            in003_count = result.result.data_array[0][0]
            print(f"✅ Total IN003 records: {in003_count}")

            if in003_count == 0:
                print("⚠️  IN003 has never been logged!")
                print("   This suggests the test query didn't write to governance table")
            else:
                print(f"✅ IN003 has {in003_count} record(s) in governance table")

                # Get the most recent IN003 record
                query5 = f"""
                SELECT
                    session_id,
                    query_string,
                    cost,
                    error_info,
                    timestamp
                FROM {governance_table}
                WHERE user_id = 'IN003'
                ORDER BY timestamp DESC
                LIMIT 1
                """

                result = w.statement_execution.execute_statement(
                    warehouse_id=SQL_WAREHOUSE_ID,
                    statement=query5,
                    wait_timeout="30s"
                )

                if result.result and result.result.data_array:
                    row = result.result.data_array[0]
                    print(f"\n📋 Most Recent IN003 Record:")
                    print(f"   Session: {row[0]}")
                    print(f"   Query: {row[1][:60]}...")
                    print(f"   Cost: ${float(row[2]):.6f}")
                    print(f"   Error Info: {'Present' if row[3] else 'None'}")
                    print(f"   Timestamp: {row[4]}")

        else:
            print("⚠️  Could not count IN003 records")

    except Exception as e:
        print(f"❌ Error checking IN003 records: {e}")

    print("\n" + "=" * 70)
    print("✅ Governance Table Check Complete")
    print("=" * 70)

if __name__ == "__main__":
    check_governance_table()
