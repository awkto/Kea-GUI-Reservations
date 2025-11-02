# Release Process

This document explains how to create production and development releases.

## Quick Reference

| Type | Tag Format | Docker Tags Created | GitHub Release |
|------|-----------|-------------------|----------------|
| **Production** | `v1.2.3` | `1.2.3`, `latest` | Full release |
| **Development** | `v1.2.3-dev` | `1.2.3-dev`, `dev` | Pre-release |

## Production Release

Use this for stable releases that go to production.

### Steps

1. **Ensure you're on main branch and up to date:**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create and push a version tag:**
   ```bash
   git tag v1.2.3
   git push origin v1.2.3
   ```

3. **What happens automatically:**
   - ✅ GitHub Actions builds Docker images for `linux/amd64` and `linux/arm64`
   - ✅ Pushes to Docker Hub with tags:
     - `awkto/kea-gui-reservations:1.2.3` (specific version)
     - `awkto/kea-gui-reservations:latest` (latest stable)
   - ✅ Updates `version.txt` in the image to `1.2.3`
   - ✅ Creates a GitHub release with auto-generated release notes
   - ✅ Application displays version as `v1.2.3` in UI

### Using the Production Image

```bash
# Pull by version
docker pull awkto/kea-gui-reservations:1.2.3

# Pull latest stable
docker pull awkto/kea-gui-reservations:latest

# Run
docker run -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  awkto/kea-gui-reservations:latest
```

---

## Development Release

Use this for testing new features before they're merged to main. Saves CI/CD minutes by only building when you explicitly create a tag.

### Steps

1. **Ensure you're on your feature branch:**
   ```bash
   git checkout feature/my-feature
   ```

2. **Create and push a dev version tag:**
   ```bash
   git tag v1.2.3-dev
   git push origin v1.2.3-dev
   ```

3. **What happens automatically:**
   - ✅ GitHub Actions builds Docker images for `linux/amd64` and `linux/arm64`
   - ✅ Pushes to Docker Hub with tags:
     - `awkto/kea-gui-reservations:1.2.3-dev` (specific dev version)
     - `awkto/kea-gui-reservations:dev` (latest dev - moving tag)
   - ✅ Updates `version.txt` in the image to `1.2.3-dev`
   - ✅ Creates a GitHub pre-release
   - ✅ Application displays version as `v1.2.3-dev` in UI
   - ❌ Does NOT update the `latest` tag (only production does this)

### Using the Dev Image

```bash
# Pull latest dev
docker pull awkto/kea-gui-reservations:dev

# Pull specific dev version
docker pull awkto/kea-gui-reservations:1.2.3-dev

# Run
docker run -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  awkto/kea-gui-reservations:dev
```

### Updating a Dev Build

If you need to rebuild the dev image with new changes:

```bash
# Make your changes and commit
git add .
git commit -m "Fix something"
git push origin feature/my-feature

# Delete and recreate the dev tag
git tag -d v1.2.3-dev
git push origin :refs/tags/v1.2.3-dev
git tag v1.2.3-dev
git push origin v1.2.3-dev
```

Or use the force flag:
```bash
git tag -f v1.2.3-dev
git push -f origin v1.2.3-dev
```

---

## Version Numbering Guidelines

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (x.0.0): Incompatible API changes
- **MINOR** version (0.x.0): New features, backward compatible
- **PATCH** version (0.0.x): Bug fixes, backward compatible

### Examples

```
v1.0.0       - First major release
v1.1.0       - Added new feature
v1.1.1       - Fixed bug
v1.2.0-dev   - Testing new feature for v1.2.0
v2.0.0-dev   - Testing breaking changes for v2.0.0
```

---

## Workflow Examples

### Example 1: Feature Development

```bash
# Create feature branch
git checkout -b feature/dhcp-config-management

# Work on feature, make commits...
git add .
git commit -m "Add DHCP configuration management"
git push origin feature/dhcp-config-management

# Ready to test Docker image
git tag v0.10.0-dev
git push origin v0.10.0-dev

# Test the image
docker pull awkto/kea-gui-reservations:dev

# Found a bug, fix it
git add .
git commit -m "Fix subnet validation"
git push origin feature/dhcp-config-management

# Rebuild dev image
git tag -f v0.10.0-dev
git push -f origin v0.10.0-dev

# Feature is ready, merge to main
git checkout main
git merge feature/dhcp-config-management
git push origin main

# Create production release
git tag v0.10.0
git push origin v0.10.0
```

### Example 2: Hotfix

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/critical-bug

# Fix the bug
git add .
git commit -m "Fix critical security issue"
git push origin hotfix/critical-bug

# Test with dev build
git tag v0.9.9-dev
git push origin v0.9.9-dev

# Verify fix works
docker pull awkto/kea-gui-reservations:dev

# Merge to main and release
git checkout main
git merge hotfix/critical-bug
git push origin main
git tag v0.9.9
git push origin v0.9.9
```

---

## Checking Build Status

### GitHub Actions
View build progress: https://github.com/awkto/kea-gui-reservations/actions

### Docker Hub
View published images: https://hub.docker.com/r/awkto/kea-gui-reservations/tags

### List All Tags
```bash
# Via Docker Hub API
curl -s "https://registry.hub.docker.com/v2/repositories/awkto/kea-gui-reservations/tags/?page_size=100" | jq -r '.results[].name' | sort -V

# Or check GitHub releases
gh release list
```

---

## Troubleshooting

### Build Failed
- Check GitHub Actions logs
- Verify Docker Hub credentials are set in repository secrets
- Check if tag format is correct (`v*.*.*` or `v*.*.*-dev`)

### Wrong Tag Created
```bash
# Delete local tag
git tag -d v1.2.3-dev

# Delete remote tag
git push origin :refs/tags/v1.2.3-dev

# Recreate with correct version
git tag v1.2.4-dev
git push origin v1.2.4-dev
```

### Need to Cancel a Release
- You can't un-push Docker images, but you can:
  1. Push a new fixed version with an incremented patch number
  2. Delete the GitHub release (images remain on Docker Hub)
  3. Add a deprecation notice to the release notes

---

## Best Practices

1. ✅ **Always test with dev builds** before creating production releases
2. ✅ **Use semantic versioning** for clear version communication
3. ✅ **Write meaningful release notes** (auto-generated, but you can edit)
4. ✅ **Tag from main branch** for production releases
5. ✅ **Delete dev tags** after merging to main (cleanup)
6. ❌ **Don't reuse version numbers** - always increment
7. ❌ **Don't tag every commit** - only when you want a Docker build

---

## CI/CD Minutes Optimization

Our workflow is optimized to minimize GitHub Actions usage:

- ✅ **No builds on every commit** - only on explicit tags
- ✅ **Build cache** enabled for faster builds
- ✅ **Multi-platform builds** in single workflow run
- ✅ **Conditional releases** (production vs dev)

### Estimated Usage
- **Production release**: ~5-8 minutes (multi-platform build)
- **Dev release**: ~3-5 minutes (with cache)
- **Free tier**: 2,000 minutes/month (sufficient for ~250-400 releases)

---

## Questions?

- **How do I know which version is running?** 
  - Check the UI (click version in navbar) or visit `/api/health`
  
- **Can I have multiple dev versions?**
  - Yes! Use different suffixes: `v1.2.3-dev`, `v1.2.3-dev2`, `v1.2.3-alpha`
  
- **What if I want to test locally without pushing?**
  - Build locally: `docker build -t kea-gui-test .`
  - No tag needed for local development

- **Should I delete old dev tags?**
  - Yes, cleanup after merging: `git push origin :refs/tags/v1.2.3-dev`
