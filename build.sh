#!/bin/bash
# build.sh - Windows-compatible build script for Render

echo "=============================================="
echo "EXCEL INTERNATIONAL ACADEMY - WINDOWS COMPATIBLE BUILD"
echo "=============================================="

# Exit on error
set -e

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "🗄️  Applying database migrations..."
python manage.py migrate --noinput

echo "📊 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🔍 Running system checks..."
python manage.py check --deploy

echo "✅ Build completed successfully!"
echo "=============================================="