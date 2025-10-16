#!/bin/bash

# Jenkins script for Auto Status Report
# This script can be used in a Jenkins job to generate status reports

set -e  # Exit on any error

echo "🚀 Starting Auto Status Report Generation..."

# Create reports directory
mkdir -p reports

# Set date variables
DATE=$(date +%Y-%m-%d)
WEEK_START=$(date -d "last monday" +%Y-%m-%d)

echo "📅 Generating reports for date: $DATE"

# Test connections first
echo "🔍 Testing connections..."
python3 main.py test

if [ $? -ne 0 ]; then
    echo "❌ Connection test failed. Exiting."
    exit 1
fi

echo "✅ Connections successful!"

# Generate weekly report (last 7 days)
echo "📊 Generating weekly report..."
python3 main.py report \
    --days 7 \
    --output "reports/weekly-report-${DATE}.md" \
    --format markdown

# Generate daily report (yesterday)
echo "📊 Generating daily report..."
python3 main.py daily \
    --output "reports/daily-report-${DATE}.md" \
    --format markdown

# Generate JSON report for data analysis
echo "📊 Generating JSON report..."
python3 main.py report \
    --days 7 \
    --output "reports/weekly-data-${DATE}.json" \
    --format json

# Generate CSV report for spreadsheet analysis
echo "📊 Generating CSV report..."
python3 main.py report \
    --days 7 \
    --output "reports/weekly-data-${DATE}.csv" \
    --format csv

# List generated files
echo "📁 Generated files:"
ls -la reports/

# Show summary
echo "📋 Report Summary:"
python3 main.py quick --days 7

echo "✅ Status report generation completed successfully!"
echo "📁 Reports saved in: reports/"

# Optional: Send notification (uncomment and configure as needed)
# echo "📧 Sending notification..."
# mail -s "Daily Development Report - $DATE" your-email@example.com < "reports/daily-report-${DATE}.md"
