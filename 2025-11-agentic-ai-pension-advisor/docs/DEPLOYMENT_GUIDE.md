# Deployment Guide

This guide walks you through setting up and running the Multi-Country Pension Advisor demo on Databricks.

## Prerequisites

- Databricks workspace (AWS, Azure, or GCP)
- Unity Catalog enabled
- SQL Warehouse (Serverless or Pro recommended)
- Foundation Model API access (Claude Sonnet 4 or similar)
- Python 3.10+

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/databricks/databricks-blogposts.git
cd databricks-blogposts/2025-11-agentic-ai-pension-advisor
```

### 2. Configure Environment

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` with your Databricks credentials:

```bash
# Databricks Configuration
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your-databricks-token

# SQL Warehouse (get from SQL Warehouses UI)
DATABRICKS_SQL_WAREHOUSE_ID=your-warehouse-id

# MLflow Experiment Paths (update with your email)
MLFLOW_EXPERIMENT_PATH=/Users/your-email@databricks.com/prod-retirement-advisory
MLFLOW_EVAL_PATH=/Users/your-email@databricks.com/retirement-eval
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Demo Notebooks

Open the notebooks in Databricks in sequence:

#### Step 1: Setup Infrastructure
```
01-setup/01_setup_infrastructure.py
```
This creates:
- Unity Catalog schemas and tables
- SQL functions (agent tools)
- Sample member data

#### Step 2: Explore the Agent
```
02-agent-demo/01_agent_basics.py
02-agent-demo/02_agent_advanced.py
```
These notebooks demonstrate:
- Basic agent queries
- Tool execution
- Multi-country capabilities

#### Step 3: Monitoring & Observability
```
03-monitoring-demo/01_mlflow_tracking.py
03-monitoring-demo/02_lakehouse_monitoring.py
```
Explore:
- MLflow experiment tracking
- Lakehouse Monitoring for governance

#### Step 4: Streamlit UI (Optional)
```
04-ui-demo/01_run_ui.py
```
Launch the interactive Streamlit interface.

### 5. Run Streamlit App Locally

```bash
# From repository root
streamlit run app.py
```

Access the UI at `http://localhost:8501`

## Configuration Details

### Unity Catalog Setup

The SQL DDLs in `sql_ddls/` create:

1. **Schema**: `super_advisory_demo`
2. **Tables**:
   - `member_profiles` - Member demographic data
   - `member_logs` - Query audit logs
   - `citation_registry` - Regulatory citations
3. **Functions** (Agent Tools):
   - `calculate_tax(member_id, amount, country)` - Tax calculations
   - `check_balance(member_id)` - Balance inquiries
   - `check_preservation_age(member_id)` - Age verification
   - `get_member_profile(member_id)` - Profile retrieval

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABRICKS_HOST` | Workspace URL | `https://dbc-abc123.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Personal access token | Get from User Settings |
| `DATABRICKS_SQL_WAREHOUSE_ID` | SQL Warehouse ID | Get from SQL Warehouses UI |
| `MLFLOW_EXPERIMENT_PATH` | Production experiment path | `/Users/email/prod-advisory` |
| `MLFLOW_EVAL_PATH` | Evaluation experiment path | `/Users/email/retirement-eval` |

### Configuration File

The `src/config/config.yaml` file contains:

- LLM endpoints and model configurations
- Temperature and token settings
- Unity Catalog connection strings
- Country-specific configurations

## Running Tests

```bash
# Run all tests
pytest

# Run specific test suites
pytest src/tests/unit/                    # Unit tests only
pytest src/tests/integration/             # Integration tests
pytest -m "country_specific"              # Country-specific tests
```

## Generating Demo Data

To generate synthetic member data using Faker:

```bash
python scripts/generate_demo_data.py --output parquet
```

This creates realistic member profiles for all supported countries (AU, US, UK, IN).

## Deployment to Databricks Apps

For production deployment, use the included `app.yaml`:

1. Upload the repository to Databricks workspace
2. Navigate to Databricks Apps
3. Create new app pointing to `app.yaml`
4. Configure environment variables in the app settings

See the [Databricks Apps documentation](https://docs.databricks.com/apps/) for details.

## Monitoring & Observability

### MLflow Tracking

All agent queries are logged to MLflow:
- Input queries and classifications
- Tool executions and results
- LLM responses and validations
- Token usage and costs

Access experiments at:
```
https://your-workspace.cloud.databricks.com/#mlflow/experiments
```

### Lakehouse Monitoring

Agent query logs are monitored for:
- Data quality (null rates, schema drift)
- Query distribution by country
- Classification accuracy
- Response time metrics

Setup monitoring in notebook:
```python
from src.observability import create_observability

obs = create_observability(enable_lakehouse_monitoring=True)
monitor = obs.setup_lakehouse_monitoring()
```

## Troubleshooting

### Issue: Import errors after reorganization

**Solution**: Ensure you're running from the repository root and `PYTHONPATH` includes the current directory:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
streamlit run app.py
```

### Issue: SQL Warehouse connection fails

**Solution**:
1. Verify SQL Warehouse is running
2. Check warehouse ID in `.env` matches the UI
3. Ensure your token has access to the warehouse

### Issue: Unity Catalog functions not found

**Solution**: Run the setup notebook `01-setup/01_setup_infrastructure.py` to create functions.

### Issue: MLflow experiments not accessible

**Solution**: Verify experiment paths in `.env` exist or create them:
```python
import mlflow
mlflow.create_experiment("/Users/your-email/prod-retirement-advisory")
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Streamlit UI (app.py)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Agent Processor (src/agent_processor.py)       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Query Classification (src/classifier.py)         │  │
│  │  2. ReAct Agentic Loop (src/react_loop.py)          │  │
│  │  3. Tool Execution (src/tools/)                      │  │
│  │  4. Response Generation (src/agents/)                │  │
│  │  5. LLM-as-Judge Validation (src/validation/)       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ▼                           ▼
┌────────────────────────┐  ┌──────────────────────────────┐
│   Unity Catalog        │  │   MLflow + Lakehouse         │
│   - Member Data        │  │   - Experiment Tracking      │
│   - SQL Functions      │  │   - Prompt Registry          │
│   - Audit Logs         │  │   - Governance Monitoring    │
└────────────────────────┘  └──────────────────────────────┘
```

## Additional Resources

- [README.md](../README.md) - Project overview and features
- [Databricks Foundation Model APIs](https://docs.databricks.com/machine-learning/foundation-models/)
- [Unity Catalog Functions](https://docs.databricks.com/sql/language-manual/sql-ref-functions.html)
- [MLflow on Databricks](https://docs.databricks.com/mlflow/)
- [Lakehouse Monitoring](https://docs.databricks.com/lakehouse-monitoring/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the demo notebooks for working examples
3. Open an issue in the [databricks-blogposts repository](https://github.com/databricks/databricks-blogposts)
