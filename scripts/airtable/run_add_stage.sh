#!/bin/bash
# Wrapper script to add Stage 1.5.8 to Airtable

# Get Airtable API key from AWS Secrets Manager
export AIRTABLE_API_KEY=$(aws secretsmanager get-secret-value --secret-id airtable_api_key --query SecretString --output text | jq -r '.api_key')

# Run the Python script
python3 /home/ubuntu/bqx-ml/scripts/airtable/add_stage_1_5_8.py
