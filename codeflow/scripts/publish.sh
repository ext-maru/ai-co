#!/bin/bash

# AI Company CodeFlow - Publish Script
# This script automates the publishing process to VS Code Marketplace

set -e

echo "🚀 AI Company CodeFlow - Publish Script"
echo "======================================"

# Check if vsce is installed
if ! command -v vsce &> /dev/null; then
    echo "❌ vsce is not installed. Installing..."
    npm install -g @vscode/vsce
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "❌ Error: You have uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Get current version from package.json
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "📦 Current version: $CURRENT_VERSION"

# Ask for new version
echo "Enter new version (current: $CURRENT_VERSION):"
read NEW_VERSION

if [ -z "$NEW_VERSION" ]; then
    echo "❌ Error: Version cannot be empty"
    exit 1
fi

# Update version in package.json
echo "📝 Updating version to $NEW_VERSION..."
npm version $NEW_VERSION --no-git-tag-version

# Update CHANGELOG.md
echo "📝 Please update CHANGELOG.md with the new version changes"
echo "Press Enter when done..."
read

# Compile and test
echo "🔨 Compiling TypeScript..."
npm run compile

echo "🧪 Running tests..."
npm test

echo "🎨 Running linter..."
npm run lint

# Build VSIX package
echo "📦 Building VSIX package..."
npm run package

# Confirm before publishing
echo ""
echo "Ready to publish version $NEW_VERSION to VS Code Marketplace"
echo "This will:"
echo "  1. Commit version changes"
echo "  2. Create git tag v$NEW_VERSION"
echo "  3. Push to GitHub"
echo "  4. Publish to VS Code Marketplace"
echo ""
echo "Continue? (y/n)"
read CONFIRM

if [ "$CONFIRM" != "y" ]; then
    echo "❌ Publishing cancelled"
    exit 1
fi

# Commit changes
echo "💾 Committing changes..."
git add .
git commit -m "Release v$NEW_VERSION"

# Create tag
echo "🏷️ Creating tag..."
git tag "v$NEW_VERSION"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main
git push origin "v$NEW_VERSION"

# Publish to marketplace
echo "🚀 Publishing to VS Code Marketplace..."
vsce publish

echo ""
echo "✅ Successfully published AI Company CodeFlow v$NEW_VERSION!"
echo ""
echo "Next steps:"
echo "  1. Check the extension on VS Code Marketplace"
echo "  2. Create GitHub release notes"
echo "  3. Announce the release"
echo ""
echo "🎉 Congratulations!"
