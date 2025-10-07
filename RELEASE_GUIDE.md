# Quick Release Guide

Follow these steps to publish a new version:

## 1. Prepare the Release

```bash
# Make sure all changes are committed
git status

# Pull latest changes
git pull origin main
```

## 2. Update Version Documentation (Optional)

Edit relevant files if needed:
- Update CHANGELOG.md with new features/fixes
- Update version references in README.md

## 3. Create and Push the Tag

```bash
# Create a version tag (use semantic versioning)
git tag v1.0.0

# Push the tag to GitHub
git push origin v1.0.0
```

## 4. Monitor the Build

1. Go to https://github.com/awkto/Kea-GUI-Reservations/actions
2. Watch the "Build and Push Docker Image" workflow
3. Wait for the green checkmark (takes ~3-5 minutes)

## 5. Verify the Release

```bash
# Pull and test the new image
docker pull awkto/kea-gui-reservations:1.0.0
docker pull awkto/kea-gui-reservations:latest

# Verify both tags work
docker run --rm awkto/kea-gui-reservations:1.0.0 --version
```

## 6. Announce the Release

The workflow automatically creates a GitHub Release with notes. You can:
- Edit the release notes on GitHub
- Announce in discussions/issues
- Update documentation

## Version Numbering

Use [Semantic Versioning](https://semver.org/):

- **Major** (v2.0.0) - Breaking changes
- **Minor** (v1.1.0) - New features, backwards compatible
- **Patch** (v1.0.1) - Bug fixes only

Examples:
```bash
git tag v1.0.0    # Initial release
git tag v1.1.0    # Added new feature
git tag v1.1.1    # Fixed a bug
git tag v2.0.0    # Breaking change
```

## Delete a Tag (if needed)

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0
```

## Common Issues

### Tag already exists
```bash
# Force update the tag
git tag -f v1.0.0
git push -f origin v1.0.0
```

### Workflow failed
- Check GitHub Actions logs for errors
- Verify Docker Hub credentials in repository secrets
- Ensure tag format is `v*.*.*`

## Quick Commands

```bash
# List all tags
git tag

# Show tag details
git show v1.0.0

# Create annotated tag with message
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push all tags
git push origin --tags
```
