# Databricks notebook source
# MAGIC %md
# MAGIC # Build Multi-Country Retirement Advisory Agent
# MAGIC
# MAGIC This notebook demonstrates how to use the production agent framework to build
# MAGIC a multi-country retirement advisory agent with:
# MAGIC - LLM-based query classification
# MAGIC - Tool calling for retirement calculations
# MAGIC - Country-specific responses
# MAGIC - Validation and quality checks
# MAGIC
# MAGIC **Agent Architecture:**
# MAGIC ```
# MAGIC User Query → Classifier → Orchestrator → Tools → Response Builder → Validated Response
# MAGIC ```

# COMMAND ----------

# MAGIC %md
# MAGIC ## Import Production Modules
# MAGIC
# MAGIC Import from root-level production code

# COMMAND ----------

import sys
import os
repo_root = os.path.abspath(
    os.path.join(os.getcwd(), "..")
)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)  # Add parent to import from root

# Import agent components
from src.agent_processor import agent_query
from src.classifier import classify_query
from src.config import MAIN_LLM_ENDPOINT, UNITY_CATALOG, UNITY_SCHEMA
from src.country_config import get_country_config, get_currency_symbol

print("✓ Agent modules imported")
print(f"  LLM Endpoint: {MAIN_LLM_ENDPOINT}")
print(f"  Unity Catalog: {UNITY_CATALOG}.{UNITY_SCHEMA}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Execute Agent Query
# MAGIC
# MAGIC The agent handles the entire flow: classification, tool execution, response synthesis, and validation

# COMMAND ----------

# Execute full agent query
import uuid

# Example query - age will be retrieved from member profile
query = "I want to know when I can access my super without penalties"
country = "AU"
member_id = "AU001"
session_id = str(uuid.uuid4())[:8]

print(f"Query: {query}")
print(f"Country: {country}")
print(f"Member: {member_id}\n")

result = agent_query(
    user_id=member_id,
    session_id=session_id,
    country=country,
    query_string=query
)

# Check for errors
if 'error' in result or 'answer' not in result:
    print("❌ Error executing query:")
    print(f"  {result.get('error', 'Unknown error')}")
    if 'Member' in str(result.get('error', '')):
        print("\n💡 Run the setup notebook first: 01-setup/01-unity-catalog-setup")
        print("   This will create sample member profiles.")
else:
    print("Agent Response:")
    print(f"{result['answer']}\n")

    print("Metadata:")
    print(f"  Tools called: {result.get('tools_called', [])}")
    print(f"  Cost: ${result.get('cost', 0):.6f}")
    print(f"  Validation: {result.get('judge_verdict', {}).get('verdict', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Multi-Country Support
# MAGIC
# MAGIC Test the agent with different countries

# COMMAND ----------

# Test queries for different countries
test_cases = [
    {
        "query": "How much tax will I pay on my retirement withdrawal?",
        "country": "AU",
        "member_id": "AU004"
    },
    {
        "query": "When can I start taking distributions from my 401(k)?",
        "country": "US",
        "member_id": "US001"
    },
    {
        "query": "What is my State Pension age?",
        "country": "UK",
        "member_id": "UK001"
    },
    {
        "query": "Can I withdraw from my EPF before age 58?",
        "country": "IN",
        "member_id": "IN001"
    }
]

# Run all test cases
for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*70}")
    print(f"Test Case {i}: {test['country']}")
    print(f"{'='*70}")
    print(f"Query: {test['query']}")
    print(f"Member: {test['member_id']}\n")

    result = agent_query(
        user_id=test['member_id'],
        session_id=str(uuid.uuid4())[:8],
        country=test['country'],
        query_string=test['query']
    )

    currency = get_currency_symbol(test['country'])
    print(f"Response ({currency}):")
    print(f"{result.get('answer', 'No response generated')[:300]}...")  # Truncate for display
    print(f"\nTools used: {result.get('tools_called', [])}")
    print(f"Cost: ${result.get('cost', 0):.6f}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Tool Integration
# MAGIC
# MAGIC The agent can call Unity Catalog functions as tools

# COMMAND ----------

# Example: Tax calculation tool
from src.tools import call_individual_tool
from src.config import SQL_WAREHOUSE_ID

# Tool call example - calculate tax for AU
tool_result = call_individual_tool(
    tool_id="tax",
    member_id="AU004",
    withdrawal_amount=50000,
    country="AU",
    warehouse_id=SQL_WAREHOUSE_ID
)

print("Tool Result:")
print(f"  Tool: {tool_result.get('tool_name', 'N/A')}")
print(f"  Calculation: {tool_result.get('calculation', 'N/A')}")
print(f"  Authority: {tool_result.get('authority', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Response Validation
# MAGIC
# MAGIC All responses go through LLM-as-a-Judge validation

# COMMAND ----------

from src.validation import validate_response

# Validate a response
validation_result = validate_response(
    query=query,
    response=result['answer'],  # Use 'answer' key from result
    country=country
)

print("Validation Result:")
print(f"  Passed: {validation_result.get('passed', False)}")
print(f"  Confidence: {validation_result.get('confidence', 0):.2f}")
print(f"  Violations: {validation_result.get('violations', [])}")
print(f"  Validator: {validation_result.get('_validator_used', 'N/A')}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Country-Specific Configuration
# MAGIC
# MAGIC Each country has specific regulations and terminology

# COMMAND ----------

import pandas as pd

# Show country configurations
countries = ['AU', 'US', 'UK', 'IN']
config_data = []

for country_code in countries:
    config = get_country_config(country_code)
    config_data.append({
        'Country': config.name,
        'Currency': f"{config.currency_symbol} {config.currency}",
        'Retirement Account': config.retirement_account_term,
        'Balance Term': config.balance_term,
        'Advisor Title': config.advisor_title
    })

config_df = pd.DataFrame(config_data)
display(config_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Complete Example: Interactive Query

# COMMAND ----------

# Interactive query example
def ask_agent(query_text, country_code, member_id):
    """Helper function to query the agent"""
    print(f"\n{'='*70}")
    print(f"QUERY ({country_code})")
    print(f"{'='*70}")
    print(f"{query_text}\n")

    result = agent_query(
        user_id=member_id,
        session_id=str(uuid.uuid4())[:8],
        country=country_code,
        query_string=query_text
    )

    print("RESPONSE:")
    print(f"{result['response']}\n")

    if result.get('citations'):
        print("CITATIONS:")
        for citation in result['citations']:
            print(f"  - {citation}")

    print(f"\nProcessing time: {result.get('processing_time', 0):.2f}s")
    print(f"Cost: ${result.get('cost', 0):.6f}")

    return result

# Example usage
result = ask_agent(
    query_text="I want to retire early. What are my options and tax implications?",
    country_code="AU",
    member_id="AU015"
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Agent Demo Complete
# MAGIC
# MAGIC You've seen how the production agent handles:
# MAGIC - Multi-country queries
# MAGIC - Tool integration
# MAGIC - Response validation
# MAGIC - Country-specific configurations
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - **03-tool-integration**: Deep dive into Unity Catalog function tools
# MAGIC - **04-validation**: LLM-as-a-Judge validation details
# MAGIC - **03-monitoring-demo/01-mlflow-tracking**: Track agent performance

# COMMAND ----------

print("✅ Agent demo complete!")
print("   Multi-country support: AU, US, UK, IN")
print("   Tool calling: Unity Catalog functions")
print("   Validation: LLM-as-a-Judge")
print("   Ready for production use")
