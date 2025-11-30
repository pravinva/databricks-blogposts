-- Migration: Add judge_confidence column to governance table
-- Run this in Databricks SQL or notebook to update existing governance table

-- Add the missing column
ALTER TABLE pension_blog.member_data.governance
ADD COLUMN judge_confidence DOUBLE COMMENT 'Validation confidence score (0.0-1.0)';

-- Verify the column was added
DESCRIBE TABLE pension_blog.member_data.governance;
