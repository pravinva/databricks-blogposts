# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Scoring Results Table
# MAGIC
# MAGIC This notebook creates the Unity Catalog table for storing automated scoring results.
# MAGIC
# MAGIC **Table:** `pension_blog.member_data.scoring_results`
# MAGIC
# MAGIC **Purpose:**
# MAGIC - Store results from automated quality scorers
# MAGIC - Enable trend analysis and quality monitoring
# MAGIC - Support Observability dashboard visualizations

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

import sys
import os

# Add project root to path
repo_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.config import UNITY_CATALOG, UNITY_SCHEMA
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

SCORING_TABLE = f"{UNITY_CATALOG}.{UNITY_SCHEMA}.scoring_results"
print(f"Creating table: {SCORING_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Table Schema

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS ${UNITY_CATALOG}.${UNITY_SCHEMA}.scoring_results (
# MAGIC   run_id STRING NOT NULL COMMENT 'MLflow run ID for the query',
# MAGIC   user_id STRING COMMENT 'User ID who made the query',
# MAGIC   country STRING COMMENT 'Country code (AU, US, UK, IN)',
# MAGIC   query_timestamp TIMESTAMP COMMENT 'When the query was made',
# MAGIC   scoring_timestamp TIMESTAMP NOT NULL COMMENT 'When the scoring was performed',
# MAGIC   overall_score DOUBLE COMMENT 'Average score across all scorers (0-1)',
# MAGIC   pass_rate DOUBLE COMMENT 'Percentage of scorers that passed',
# MAGIC   passed_count INT COMMENT 'Number of scorers that passed',
# MAGIC   total_count INT COMMENT 'Total number of scorers run',
# MAGIC   verdict STRING COMMENT 'Overall verdict (PASS, FAIL, ERROR)',
# MAGIC   individual_scores STRING COMMENT 'JSON string with individual scorer results'
# MAGIC )
# MAGIC USING DELTA
# MAGIC COMMENT 'Automated quality scoring results for production queries'
# MAGIC TBLPROPERTIES (
# MAGIC   'delta.enableChangeDataFeed' = 'true',
# MAGIC   'delta.autoOptimize.optimizeWrite' = 'true',
# MAGIC   'delta.autoOptimize.autoCompact' = 'true'
# MAGIC )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Table Creation

# COMMAND ----------

# MAGIC %sql
# MAGIC DESCRIBE TABLE EXTENDED ${UNITY_CATALOG}.${UNITY_SCHEMA}.scoring_results

# COMMAND ----------

# MAGIC %md
# MAGIC ## Create Sample Data (Optional)

# COMMAND ----------

from datetime import datetime, timedelta
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
import json

# Create sample data for testing
sample_data = []
base_time = datetime.now() - timedelta(days=7)

for i in range(20):
    query_time = base_time + timedelta(hours=i * 3)
    scoring_time = query_time + timedelta(minutes=30)

    # Simulate varying quality scores
    overall_score = 0.75 + (i % 5) * 0.05
    pass_rate = 0.8 if overall_score > 0.7 else 0.6

    sample_data.append({
        'run_id': f'sample_run_{i:03d}',
        'user_id': f'AU{(i % 10):03d}',
        'country': ['AU', 'US', 'UK', 'IN'][i % 4],
        'query_timestamp': query_time,
        'scoring_timestamp': scoring_time,
        'overall_score': overall_score,
        'pass_rate': pass_rate,
        'passed_count': 4 if overall_score > 0.7 else 3,
        'total_count': 5,
        'verdict': 'PASS' if overall_score > 0.7 else 'FAIL',
        'individual_scores': json.dumps({
            'relevance': {'score': overall_score, 'passed': True},
            'faithfulness': {'score': overall_score + 0.1, 'passed': True},
            'toxicity': {'score': 1.0, 'passed': True},
            'country_compliance': {'score': overall_score - 0.1, 'passed': overall_score > 0.6},
            'citation_quality': {'score': overall_score, 'passed': overall_score > 0.7}
        })
    })

schema = StructType([
    StructField("run_id", StringType(), False),
    StructField("user_id", StringType(), True),
    StructField("country", StringType(), True),
    StructField("query_timestamp", TimestampType(), True),
    StructField("scoring_timestamp", TimestampType(), False),
    StructField("overall_score", DoubleType(), True),
    StructField("pass_rate", DoubleType(), True),
    StructField("passed_count", IntegerType(), True),
    StructField("total_count", IntegerType(), True),
    StructField("verdict", StringType(), True),
    StructField("individual_scores", StringType(), True)
])

sample_df = spark.createDataFrame(sample_data, schema)

# Write sample data
sample_df.write \
    .format("delta") \
    .mode("append") \
    .saveAsTable(SCORING_TABLE)

print(f"✅ Added {sample_df.count()} sample records to {SCORING_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Query Sample Data

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT
# MAGIC   country,
# MAGIC   COUNT(*) as total_queries,
# MAGIC   AVG(overall_score) as avg_score,
# MAGIC   AVG(pass_rate) as avg_pass_rate,
# MAGIC   SUM(CASE WHEN verdict = 'PASS' THEN 1 ELSE 0 END) / COUNT(*) as pass_percentage
# MAGIC FROM ${UNITY_CATALOG}.${UNITY_SCHEMA}.scoring_results
# MAGIC GROUP BY country
# MAGIC ORDER BY country

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary

# COMMAND ----------

# MAGIC %md
# MAGIC ### Table Setup Complete ✅
# MAGIC
# MAGIC The `scoring_results` table is now ready to:
# MAGIC 1. ✅ Store automated scoring results
# MAGIC 2. ✅ Enable trend analysis
# MAGIC 3. ✅ Support Observability dashboard
# MAGIC 4. ✅ Track quality metrics over time
# MAGIC
# MAGIC **Next Steps:**
# MAGIC - Run automated scoring job (notebook 09)
# MAGIC - View results in Observability page
# MAGIC - Set up alerting based on quality thresholds
# MAGIC
# MAGIC **Table Location:** `pension_blog.member_data.scoring_results`
# MAGIC
# MAGIC **Sample Queries:**
# MAGIC ```sql
# MAGIC -- Recent quality trend
# MAGIC SELECT DATE(scoring_timestamp) as day, AVG(overall_score) as avg_score
# MAGIC FROM pension_blog.member_data.scoring_results
# MAGIC WHERE scoring_timestamp >= CURRENT_DATE - INTERVAL 7 DAYS
# MAGIC GROUP BY day
# MAGIC ORDER BY day;
# MAGIC
# MAGIC -- Quality by country
# MAGIC SELECT country, AVG(overall_score), AVG(pass_rate)
# MAGIC FROM pension_blog.member_data.scoring_results
# MAGIC GROUP BY country;
# MAGIC
# MAGIC -- Recent failures
# MAGIC SELECT run_id, country, overall_score, verdict, individual_scores
# MAGIC FROM pension_blog.member_data.scoring_results
# MAGIC WHERE verdict = 'FAIL'
# MAGIC ORDER BY scoring_timestamp DESC
# MAGIC LIMIT 10;
# MAGIC ```
