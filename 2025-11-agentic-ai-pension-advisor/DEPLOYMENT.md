# Deploying to Databricks Apps

This guide explains how to deploy the Retirement Advisory Agent to Databricks Apps.

## Prerequisites

- ✅ Databricks workspace (<your-workspace>.cloud.databricks.com)
- ✅ Unity Catalog configured (`pension_blog.member_data`)
- ✅ SQL Warehouse ID: `4b9b953939869799`
- ✅ Code pushed to GitHub: https://github.com/pravinva/databricks-blogposts

## Deployment Options

### Option 1: Databricks Apps UI (Recommended) ⭐

#### Step 1: Set Up Secrets (One-time)

1. In Databricks workspace, go to **Settings** → **Developer** → **Secrets**
2. Click **Create Scope**
   - Scope name: `pension_blog`
3. Add secrets:
   - `databricks_host`: `https://<your-workspace>.cloud.databricks.com`
   - `databricks_token`: `<your-databricks-token>`

**Alternative: Use Databricks CLI**
```bash
databricks secrets create-scope pension_blog
databricks secrets put-secret pension_blog databricks_host --string-value "https://<your-workspace>.cloud.databricks.com"
databricks secrets put-secret pension_blog databricks_token --string-value "<your-databricks-token>"
```

#### Step 2: Create Databricks Repo (If not done)

1. Go to **Repos** → **Add Repo**
2. Git repository URL: `https://github.com/pravinva/databricks-blogposts`
3. Click **Create Repo**

#### Step 3: Deploy App

1. Go to **Compute** → **Apps**
2. Click **Create App**
3. Configure:
   - **Name**: `Retirement Advisory Agent`
   - **Source Type**: Workspace
   - **Source Path**: `/Repos/<your-username>/databricks-blogposts/2025-11-agentic-ai-pension-advisor`
   - **App Configuration**: `app.yaml`
4. Click **Create**
5. Wait 2-3 minutes for deployment

#### Step 4: Access App

- App URL: `https://<your-workspace>.cloud.databricks.com/apps/<app-id>`
- Share URL with team members
- App automatically uses Databricks authentication

---

### Option 2: Databricks Asset Bundles (DABs)

For production deployments with CI/CD:

#### Step 1: Install Databricks CLI

```bash
pip install databricks-cli
```

#### Step 2: Configure Authentication

```bash
databricks configure --host https://<your-workspace>.cloud.databricks.com
# Enter your token when prompted
```

#### Step 3: Create Bundle Configuration

Create `databricks.yml`:

```yaml
bundle:
  name: retirement-advisory-agent

resources:
  apps:
    retirement-advisory:
      name: "Retirement Advisory Agent"
      source_code_path: "."
      config:
        command: ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
        env:
          - name: DATABRICKS_SQL_WAREHOUSE_ID
            value: "4b9b953939869799"
          - name: UNITY_CATALOG
            value: "pension_blog"
          - name: UNITY_SCHEMA
            value: "member_data"

targets:
  dev:
    mode: development
    workspace:
      host: https://<your-workspace>.cloud.databricks.com

  prod:
    mode: production
    workspace:
      host: https://<your-workspace>.cloud.databricks.com
```

#### Step 4: Deploy

```bash
# Deploy to dev
databricks bundle deploy --target dev

# Deploy to prod
databricks bundle deploy --target prod
```

---

## Configuration Files

### app.yaml

Already configured at project root:

```yaml
command: ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

env:
  - name: DATABRICKS_HOST
    value: "{{secrets/pension_blog/databricks_host}}"
  - name: DATABRICKS_TOKEN
    value: "{{secrets/pension_blog/databricks_token}}"
  - name: DATABRICKS_SQL_WAREHOUSE_ID
    value: "4b9b953939869799"
  - name: MLFLOW_EXPERIMENT_PATH
    value: "/Users/pravin.varma@databricks.com/pension-blog-prod"
  - name: UNITY_CATALOG
    value: "pension_blog"
  - name: UNITY_SCHEMA
    value: "member_data"
```

### requirements.txt

Dependencies automatically installed:

```
streamlit==1.51.0
mlflow>=2.8.0
databricks-sdk>=0.12.0
pandas>=2.0.0
plotly>=5.14.0
pydantic>=2.0.0
PyYAML>=6.0.0
Jinja2>=3.1.0
```

---

## Verify Deployment

### Test App Health

1. Open app URL
2. Select country (AU, US, UK, IN)
3. Select member from dropdown
4. Run example query
5. Verify response displays with:
   - ✅ Agent response
   - ✅ Citations
   - ✅ Validation status
   - ✅ Performance metrics

### Monitor App

1. **MLflow Tracking**
   - Go to MLflow experiments
   - Path: `/Users/pravin.varma@databricks.com/pension-blog-prod`
   - View query metrics, costs, validation results

2. **Governance Dashboard**
   - Run notebook: `03-monitoring-demo/03-dashboard.py`
   - View audit logs, compliance reports

3. **App Logs**
   - In Apps UI → Click on your app → Logs tab
   - Monitor errors, performance

---

## Troubleshooting

### Issue: App fails to start

**Check:**
- ✅ Secrets configured correctly
- ✅ SQL Warehouse ID valid
- ✅ Unity Catalog tables exist
- ✅ All dependencies in requirements.txt

**Solution:**
```bash
# Check logs
databricks apps logs <app-id>

# Verify secrets
databricks secrets list-secrets pension_blog
```

### Issue: Authentication errors

**Check:**
- ✅ DATABRICKS_HOST correct
- ✅ DATABRICKS_TOKEN valid
- ✅ Token has necessary permissions

**Solution:**
```bash
# Regenerate token
# Settings → Developer → Access Tokens → Generate New Token
```

### Issue: SQL queries fail

**Check:**
- ✅ SQL Warehouse running
- ✅ Unity Catalog permissions granted
- ✅ Tables exist in `pension_blog.member_data`

**Solution:**
```sql
-- Verify tables exist
SHOW TABLES IN pension_blog.member_data;

-- Check permissions
SHOW GRANT ON CATALOG pension_blog;
```

---

## Updating Deployed App

### Method 1: Auto-sync from Git

1. Push changes to GitHub
2. In Databricks Repos → Pull latest
3. App auto-restarts with new code

### Method 2: Redeploy

1. Go to Apps UI
2. Find your app
3. Click **Restart** or **Update**

### Method 3: CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Databricks Apps

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Databricks CLI
        run: pip install databricks-cli

      - name: Deploy App
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
        run: |
          databricks bundle deploy --target prod
```

---

## Production Checklist

Before going to production:

- [ ] Secrets configured in production workspace
- [ ] Unity Catalog tables populated with real data
- [ ] SQL Warehouse sized appropriately
- [ ] MLflow experiments created
- [ ] Row-level security enabled
- [ ] User authentication configured
- [ ] Monitoring dashboards set up
- [ ] Error alerting configured
- [ ] Load testing completed
- [ ] Security review passed
- [ ] Documentation updated

---

## Support

**Issues?**
- Check logs: Apps UI → Your App → Logs
- Run health check: `python3 test_full_notebook.py`
- Review notebooks: `02-agent-demo/02-build-agent.py`

**Contact:**
- GitHub Issues: https://github.com/pravinva/databricks-blogposts/issues
- Databricks Support: support@databricks.com

---

## Next Steps

1. ✅ Deploy app to dev environment
2. ✅ Test with sample data
3. ✅ Set up monitoring
4. ✅ Deploy to production
5. ✅ Share with team

**App Features:**
- 🌍 Multi-country support (AU, US, UK, IN)
- 🤖 AI-powered retirement advice
- 📊 Real-time validation
- 💰 Cost tracking
- 📈 MLflow monitoring
- 🔒 Secure with row-level security

**Ready to deploy!** 🚀
