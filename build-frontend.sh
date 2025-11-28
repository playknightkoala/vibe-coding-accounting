#!/bin/bash
# Frontend build script for production deployment

set -e  # Exit on error

echo "========================================="
echo "Building Frontend for Production"
echo "========================================="

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
else
    echo "Dependencies already installed, skipping..."
fi

# Build for production
echo "Building production bundle..."
npm run build:prod

# Check if build was successful
if [ -d "dist" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "Output directory: frontend/dist/"
    echo ""
    echo "Files created:"
    ls -lh dist/
    echo ""
    echo "You can now deploy with:"
    echo "  docker-compose -f docker-compose.prod.yml up -d --build"
else
    echo ""
    echo "❌ Build failed! dist/ directory not found."
    exit 1
fi

cd ..
