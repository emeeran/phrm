#!/bin/bash

# PHRM Optimization Setup Script

# Display header
echo "=========================================="
echo "  PHRM Project Optimization Setup"
echo "=========================================="

# Check for virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Warning: It appears you're not using a virtual environment."
  echo "It's recommended to activate a virtual environment before continuing."
  read -p "Continue anyway? (y/n): " CONT
  if [ "$CONT" != "y" ]; then
    echo "Exiting setup."
    exit 0
  fi
else
  echo "✓ Virtual environment active: $VIRTUAL_ENV"
fi

# Install dependencies
echo -e "\n[1/4] Installing dependencies..."
pip install -r requirements.txt

# Install dev dependencies if requested
read -p "Install development dependencies? (y/n): " DEVDEPS
if [ "$DEVDEPS" = "y" ]; then
  pip install -r requirements-dev.txt
  echo "✓ Development dependencies installed"
else
  echo "✓ Skipping development dependencies"
fi

# Apply migrations
echo -e "\n[2/4] Applying database migrations..."
flask db upgrade
echo "✓ Database migrations applied"

# Compile static assets
echo -e "\n[3/4] Optimizing static assets..."

# Create directories if they don't exist
mkdir -p app/static/js/dist
mkdir -p app/static/css/dist

# Check if npm is installed for optional asset optimization
if command -v npm &>/dev/null; then
  read -p "Optimize assets with npm? This will install required packages. (y/n): " OPTIMIZE
  
  if [ "$OPTIMIZE" = "y" ]; then
    # Create temporary package.json if it doesn't exist
    if [ ! -f "package.json" ]; then
      echo '{
        "name": "phrm",
        "version": "1.0.0",
        "description": "Personal Health Record Manager",
        "scripts": {
          "build:js": "terser app/static/js/*.js -o app/static/js/dist/bundle.min.js -c -m",
          "build:css": "postcss app/static/css/*.css -o app/static/css/dist/bundle.min.css"
        }
      }' > package.json
      
      # Install optimization tools
      npm install --save-dev terser postcss postcss-cli postcss-import cssnano
      
      # Create postcss config
      echo "module.exports = {
        plugins: [
          require('postcss-import'),
          require('cssnano')({preset: 'default'})
        ]
      }" > postcss.config.js
      
      # Build assets
      npm run build:js
      npm run build:css
      
      echo "✓ Assets optimized and minified to dist/ directories"
    else
      echo "! package.json exists, skipping automatic asset optimization"
    fi
  else
    echo "✓ Skipping asset optimization"
  fi
else
  echo "! npm not found, skipping asset optimization"
fi

# Final setup
echo -e "\n[4/4] Finalizing setup..."

# Create logs directory if it doesn't exist
mkdir -p logs
touch logs/app.log
echo "✓ Log files created"

# Set proper permissions
chmod +x run.py
echo "✓ Executable permissions set"

echo -e "\n=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo "To run the application:"
echo "  flask run"
echo "  or"
echo "  python run.py"
echo "=========================================="
