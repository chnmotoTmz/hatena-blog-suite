#!/bin/bash
# Minimal setup script

echo "Setting up Hatena Blog Suite - Minimal Edition"

# Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements-minimal.txt

# Node.js dependencies
echo "Installing Node.js dependencies..."
npm install --production

echo "Setup complete!"
echo "Usage:"
echo "  python cli.py --blog-id your_id"
echo "  npm start  # for MCP server"
