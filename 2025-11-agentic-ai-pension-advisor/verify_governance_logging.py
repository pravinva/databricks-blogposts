#!/usr/bin/env python3
"""
Verify governance table logging - Check Fix #1 (no duplicates) and Fix #6 (cost metadata)
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from databricks.sdk import WorkspaceClient
from src.config import SQL_WAREHOUSE_ID, get_governance_table_path
import json

def verify_governance_logging():
    """Check governance table for the test query"""
    print("=" * 70)
    print("🔍 Verifying Governance Table Logging")
    print("=" * 70)

    w = WorkspaceClient()
    governance_table = get_governance_table_path()

    print(f"\n📊 Governance Table: {governance_table}")
    print(f"🔧 SQL Warehouse: {SQL_WAREHOUSE_ID}")

    # Query for IN003 entries in the last 5 minutes
    query = f"""
    SELECT
        session_id,
        user_id,
        country,
        query_string,
        cost,
        error_info,
        timestamp
    FROM {governance_table}
    WHERE user_id = 'IN003'
    AND timestamp >= current_timestamp() - INTERVAL 5 MINUTES
    ORDER BY timestamp DESC
    LIMIT 5
    """

    print(f"\n📝 SQL Query:")
    print("-" * 70)
    print(query)
    print("-" * 70)

    try:
        print("\n🔄 Executing query...")
        result = w.statement_execution.execute_statement(
            warehouse_id=SQL_WAREHOUSE_ID,
            statement=query,
            wait_timeout="30s"
        )

        if result.result and result.result.data_array:
            rows = result.result.data_array
            print(f"\n✅ Found {len(rows)} record(s) for IN003")

            if len(rows) > 1:
                print(f"\n❌ DUPLICATE LOGGING DETECTED! (Fix #1 Failed)")
                print(f"   Expected: 1 record")
                print(f"   Found: {len(rows)} records")
                print(f"   This means the duplicate logging was NOT removed!")
            else:
                print(f"\n✅ FIX #1 VERIFIED: Only 1 record (no duplicates)")

            print("\n" + "=" * 70)
            print("📋 GOVERNANCE TABLE RECORDS")
            print("=" * 70)

            for i, row in enumerate(rows, 1):
                print(f"\n🔹 Record {i}:")
                print(f"   Session ID: {row[0]}")
                print(f"   User ID: {row[1]}")
                print(f"   Country: {row[2]}")
                print(f"   Query: {row[3][:60]}...")
                print(f"   Cost: ${float(row[4]):.6f}")

                # Check Fix #6: Cost metadata in error_info
                error_info = row[5]
                if error_info:
                    print(f"\n   📦 Error Info (Fix #6):")
                    try:
                        cost_metadata = json.loads(error_info)
                        print(f"   ✅ Cost metadata found:")
                        print(f"      Classification Cost: ${cost_metadata.get('classification_cost', 0):.6f}")
                        print(f"      Classification Method: {cost_metadata.get('classification_method', 'N/A')}")
                        print(f"      Synthesis Cost: ${cost_metadata.get('synthesis_cost', 0):.6f}")
                        print(f"      Validation Cost: ${cost_metadata.get('validation_cost', 0):.6f}")
                        print(f"      Total Cost: ${cost_metadata.get('total_cost', 0):.6f}")
                        print(f"\n   ✅ FIX #6 VERIFIED: Cost metadata stored correctly")
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Not JSON: {error_info}")
                        print(f"   ❌ FIX #6 FAILED: Cost metadata not in JSON format")
                else:
                    print(f"   ⚠️  Error Info: None")
                    print(f"   ❌ FIX #6 FAILED: No cost metadata stored")

                print(f"   Timestamp: {row[6]}")

            # Summary
            print("\n" + "=" * 70)
            print("✅ GOVERNANCE LOGGING VERIFICATION COMPLETE")
            print("=" * 70)
            print(f"Fix #1 (No Duplicates): {'✅ PASS' if len(rows) == 1 else '❌ FAIL'}")

            # Check Fix #6 for first record
            if rows and rows[0][5]:
                try:
                    json.loads(rows[0][5])
                    print(f"Fix #6 (Cost Metadata): ✅ PASS")
                except:
                    print(f"Fix #6 (Cost Metadata): ❌ FAIL")
            else:
                print(f"Fix #6 (Cost Metadata): ❌ FAIL (no error_info)")

            return len(rows) == 1  # Success if exactly 1 record

        else:
            print("\n⚠️  No records found for IN003 in the last 5 minutes")
            print("   This could mean:")
            print("   1. Governance logging failed completely")
            print("   2. The query was too old (>5 minutes)")
            print("   3. The table doesn't exist or is in a different location")
            return False

    except Exception as e:
        print(f"\n❌ Error querying governance table: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_governance_logging()
    sys.exit(0 if success else 1)
