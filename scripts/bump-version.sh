#!/usr/bin/env bash
# Usage: ./scripts/bump-version.sh 0.4.0
set -euo pipefail

VERSION="${1:?Usage: bump-version.sh <version>}"

echo "Bumping all packages to $VERSION"

# Root VERSION file
echo "$VERSION" > VERSION

# Python packages
sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" \
  engine/pyproject.toml \
  api/pyproject.toml \
  sdks/python/pyproject.toml

# Python SDK __version__
sed -i '' "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" \
  sdks/python/openbiometrics_sdk/__init__.py

# Node.js SDK
cd packages/sdk && npm version "$VERSION" --no-git-tag-version && cd ../..

# FastAPI app version
sed -i '' "s/version=\".*\"/version=\"$VERSION\"/" api/app/main.py

# Internal packages (dashboard, www)
for pkg in packages/dashboard packages/www; do
  cd "$pkg" && npm version "$VERSION" --no-git-tag-version && cd ../..
done

echo "Done. All packages at $VERSION"
echo "Don't forget to: git add -A && git commit -m 'release: v$VERSION' && git tag v$VERSION"
