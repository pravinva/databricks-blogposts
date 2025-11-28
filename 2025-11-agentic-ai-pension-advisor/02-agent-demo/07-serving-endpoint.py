# Databricks notebook source
# MAGIC %md
# MAGIC # Serving Endpoint Deployment (Optional)
# MAGIC
# MAGIC This notebook demonstrates **optional** deployment of the pension advisor model as a serving endpoint.
# MAGIC
# MAGIC **⚠️ IMPORTANT: This notebook must be run in Databricks workspace**
# MAGIC - Requires `dbutils`, `spark`, and `display()` functions
# MAGIC - Cannot run as local Python script
# MAGIC - Needs Databricks workspace authentication
# MAGIC
# MAGIC **When to Use Serving Endpoints:**
# MAGIC - **Real-time inference** requirements (< 100ms latency)
# MAGIC - **High throughput** scenarios (1000s queries/second)
# MAGIC - **REST API** access from external applications
# MAGIC
# MAGIC **When NOT to Use:**
# MAGIC - **Batch processing** (use `mlflow.pyfunc.load_model()` instead)
# MAGIC - **Low query volume** (< 100 queries/hour)
# MAGIC - **Cost-sensitive** deployments (endpoints run 24/7)
# MAGIC
# MAGIC **For This Use Case:**
# MAGIC The pension advisor is designed for **batch processing** and **on-demand queries** in Databricks UI.
# MAGIC Serving endpoints are optional and recommended only if you need external API access.
# MAGIC
# MAGIC **Architecture:**
# MAGIC ```
# MAGIC Unity Catalog Model → Serving Endpoint → REST API
# MAGIC                     ↓
# MAGIC                 Inference Tables (auto-logging)
# MAGIC                     ↓
# MAGIC                 Lakehouse Monitoring
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup

# COMMAND ----------

import sys
import os

# Add project root to path
repo_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    ServedEntityInput,
    EndpointCoreConfigInput,
    AutoCaptureConfigInput
)
from src.config import UNITY_CATALOG, UNITY_SCHEMA

# Initialize Databricks workspace client
w = WorkspaceClient()

# Configuration
ENDPOINT_NAME = "pension-advisor"
MODEL_NAME = f"{UNITY_CATALOG}.{UNITY_SCHEMA}.pension_advisor"
WORKLOAD_SIZE = "Small"  # Small, Medium, Large
SCALE_TO_ZERO = True  # Enable scale-to-zero for cost savings

print(f"Endpoint Name: {ENDPOINT_NAME}")
print(f"Model: {MODEL_NAME}")
print(f"Workload Size: {WORKLOAD_SIZE}")
print(f"Scale to Zero: {SCALE_TO_ZERO}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check if Endpoint Exists

# COMMAND ----------

try:
    existing_endpoint = w.serving_endpoints.get(ENDPOINT_NAME)
    print(f"✅ Endpoint '{ENDPOINT_NAME}' already exists")
    print(f"   Status: {existing_endpoint.state.config_update}")
    print(f"   URL: {existing_endpoint.url}")
    endpoint_exists = True
except Exception as e:
    print(f"📝 Endpoint '{ENDPOINT_NAME}' does not exist yet")
    endpoint_exists = False

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Serving Endpoint
# MAGIC
# MAGIC **Note:** This will create a 24/7 running endpoint. Consider cost implications.

# COMMAND ----------

if not endpoint_exists:
    print(f"Creating serving endpoint '{ENDPOINT_NAME}'...")
    print(f"⏱️  This may take 5-10 minutes...")

    try:
        endpoint = w.serving_endpoints.create(
            name=ENDPOINT_NAME,
            config=EndpointCoreConfigInput(
                name=ENDPOINT_NAME,  # Add name parameter to config
                served_entities=[
                    ServedEntityInput(
                        entity_name=MODEL_NAME,
                        entity_version="1",  # Or use alias: @champion
                        scale_to_zero_enabled=SCALE_TO_ZERO,
                        workload_size=WORKLOAD_SIZE,
                        workload_type="CPU"  # CPU or GPU
                    )
                ],
                # Enable automatic inference table logging
                auto_capture_config=AutoCaptureConfigInput(
                    catalog_name=UNITY_CATALOG,
                    schema_name=UNITY_SCHEMA,
                    table_name_prefix="pension_advisor"
                )
            )
        )

        print(f"✅ Endpoint created successfully!")
        print(f"   Name: {endpoint.name}")
        print(f"   URL: {endpoint.url}")
        print(f"   Inference tables will be created at:")
        print(f"   - {UNITY_CATALOG}.{UNITY_SCHEMA}.pension_advisor_payload")
        print(f"   - {UNITY_CATALOG}.{UNITY_SCHEMA}.pension_advisor_assessment")

    except Exception as e:
        print(f"❌ Failed to create endpoint: {str(e)}")
        raise
else:
    print("⏭️  Skipping creation - endpoint already exists")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Wait for Endpoint to be Ready

# COMMAND ----------

import time

print(f"Waiting for endpoint '{ENDPOINT_NAME}' to be ready...")

max_wait = 600  # 10 minutes
start_time = time.time()

while time.time() - start_time < max_wait:
    try:
        endpoint = w.serving_endpoints.get(ENDPOINT_NAME)
        state = endpoint.state.config_update

        if state == "NOT_UPDATING":
            print(f"✅ Endpoint is ready!")
            print(f"   URL: {endpoint.url}")
            break
        else:
            print(f"   Status: {state} - waiting...")
            time.sleep(30)

    except Exception as e:
        print(f"   Error checking status: {e}")
        time.sleep(30)

else:
    print("⚠️  Timeout waiting for endpoint to be ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test Endpoint with Sample Query

# COMMAND ----------

import requests
import json
import os
from src.utils.lakehouse import execute_sql_query
from src.config import get_member_profiles_table_path

# Get real member ID from database
def get_test_member_id(country='AU'):
    """Get first real member ID for testing"""
    try:
        table_path = get_member_profiles_table_path()
        query = f"SELECT member_id FROM {table_path} WHERE country = '{country}' LIMIT 1"
        df = execute_sql_query(query)
        if not df.empty:
            return df['member_id'].iloc[0]
    except:
        pass
    return f"{country}001"  # Fallback

test_member_id = get_test_member_id('AU')
print(f"Using test member ID: {test_member_id}")

# Get authentication token
token = os.environ.get("DATABRICKS_TOKEN") or dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# Get endpoint URL
endpoint = w.serving_endpoints.get(ENDPOINT_NAME)
endpoint_url = endpoint.url

# Sample query with real member ID
test_query = {
    "dataframe_records": [{
        "user_id": test_member_id,
        "session_id": "test-session",
        "country": "AU",
        "query": "What is my preservation age?",
        "validation_mode": "llm_judge",
        "enable_observability": False
    }]
}

print("Testing endpoint with sample query...")
print(f"URL: {endpoint_url}/invocations")

try:
    response = requests.post(
        f"{endpoint_url}/invocations",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json=test_query,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        print("\n✅ Endpoint test successful!")
        print(f"   Answer: {result['predictions'][0]['answer'][:100]}...")
        print(f"   Cost: ${result['predictions'][0]['cost']:.6f}")
        print(f"   Blocked: {result['predictions'][0]['blocked']}")
    else:
        print(f"\n❌ Endpoint test failed: HTTP {response.status_code}")
        print(f"   Response: {response.text}")

except Exception as e:
    print(f"\n❌ Endpoint test failed: {str(e)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Check Inference Tables
# MAGIC
# MAGIC Inference tables are automatically created and populated by the serving endpoint.

# COMMAND ----------

# Check if inference tables exist
payload_table = f"{UNITY_CATALOG}.{UNITY_SCHEMA}.pension_advisor_payload"
assessment_table = f"{UNITY_CATALOG}.{UNITY_SCHEMA}.pension_advisor_assessment"

print("Checking inference tables...")

try:
    payload_df = spark.table(payload_table)
    print(f"\n✅ Payload table exists: {payload_table}")
    print(f"   Rows: {payload_df.count()}")
    print(f"   Schema: {', '.join([f.name for f in payload_df.schema])}")

    print(f"\nSample payload:")
    display(payload_df.limit(5))

except Exception as e:
    print(f"\n⚠️  Payload table not yet created: {payload_table}")
    print(f"   (Tables are created after first request)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configure Lakehouse Monitoring on Inference Table

# COMMAND ----------

from databricks.sdk.service.catalog import MonitorInferenceProfile, MonitorCronSchedule

print("Setting up Lakehouse Monitoring on inference table...")

try:
    monitor = w.quality_monitors.create(
        table_name=payload_table,
        assets_dir=f"/Workspace/Users/{w.current_user.me().user_name}/monitors",
        output_schema_name=UNITY_SCHEMA,
        inference_profile=MonitorInferenceProfile(
            prediction_col="predictions",
            timestamp_col="timestamp",
            granularities=["1 day"],
            problem_type="PROBLEM_TYPE_REGRESSION"  # or CLASSIFICATION
        ),
        schedule=MonitorCronSchedule(
            quartz_cron_expression="0 0 9 * * ?",  # Daily at 9am
            timezone_id="UTC"
        )
    )

    print(f"✅ Monitor created successfully!")
    print(f"   Monitor ID: {monitor.monitor_name}")

except Exception as e:
    print(f"⚠️  Monitor creation: {str(e)}")
    print(f"   (May already exist or table not ready)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Get Endpoint URL for External Use

# COMMAND ----------

endpoint = w.serving_endpoints.get(ENDPOINT_NAME)

print("Endpoint Information:")
print("=" * 70)
print(f"Name: {endpoint.name}")
print(f"URL: {endpoint.url}")
print(f"Status: {endpoint.state.config_update}")
print(f"\nInference Tables:")
print(f"  - Payload: {payload_table}")
print(f"  - Assessment: {assessment_table}")
print(f"\nTo call this endpoint:")
print(f"  POST {endpoint.url}/invocations")
print(f"  Headers: Authorization: Bearer <token>")
print(f"  Body: {json.dumps(test_query, indent=2)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Estimated Cost Analysis

# COMMAND ----------

print("Serving Endpoint Cost Estimate (Approximate)")
print("=" * 70)

workload_costs = {
    "Small": 0.40,  # $/hour
    "Medium": 0.80,
    "Large": 1.60
}

hourly_cost = workload_costs.get(WORKLOAD_SIZE, 0.40)
daily_cost = hourly_cost * 24
monthly_cost = daily_cost * 30

print(f"\nWorkload Size: {WORKLOAD_SIZE}")
print(f"Scale to Zero: {SCALE_TO_ZERO}")
print(f"\nCosts (if running continuously):")
print(f"  Hourly: ${hourly_cost:.2f}")
print(f"  Daily: ${daily_cost:.2f}")
print(f"  Monthly: ${monthly_cost:.2f}")

if SCALE_TO_ZERO:
    print(f"\n💰 With scale-to-zero enabled:")
    print(f"   - Endpoint scales down when idle (no queries)")
    print(f"   - You only pay for compute time used")
    print(f"   - Cold start: ~30-60 seconds")

print(f"\n📊 Alternative: Batch Inference")
print(f"   - Use mlflow.pyfunc.load_model() directly")
print(f"   - Pay only for query execution time")
print(f"   - No 24/7 endpoint costs")
print(f"   - Recommended for < 100 queries/hour")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Delete Endpoint (Cost Savings)
# MAGIC
# MAGIC **Run this cell to delete the endpoint if not needed.**

# COMMAND ----------

# Uncomment to delete endpoint
# print(f"Deleting endpoint '{ENDPOINT_NAME}'...")
# w.serving_endpoints.delete(ENDPOINT_NAME)
# print(f"✅ Endpoint deleted")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary: Serving Endpoint
# MAGIC
# MAGIC **What We Accomplished:**
# MAGIC - ✅ (Optional) Created serving endpoint for real-time inference
# MAGIC - ✅ Configured inference tables for auto-logging
# MAGIC - ✅ Set up Lakehouse Monitoring
# MAGIC - ✅ Tested endpoint with sample query
# MAGIC - ✅ Reviewed cost implications
# MAGIC
# MAGIC **Recommendation:**
# MAGIC For the pension advisor use case with on-demand queries:
# MAGIC - ✅ **Use batch inference** with `mlflow.pyfunc.load_model()`
# MAGIC - ❌ **Skip serving endpoint** (unless you need external API access)
# MAGIC - 💰 **Save costs** by avoiding 24/7 endpoint
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - Review Phase 3 completion documentation
# MAGIC - Monitor inference tables (if endpoint deployed)
# MAGIC - Use Databricks native UIs (links in sidebar)
