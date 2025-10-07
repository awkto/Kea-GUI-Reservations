# CI/CD Setup Guide

This project uses GitHub Actions to automatically build and publish Docker images to Docker Hub when you create version tags.

## Prerequisites

1. A Docker Hub account
2. A Docker Hub repository (e.g., `awkto/kea-gui-reservations`)

## Setup Instructions

### Step 1: Configure Docker Hub Repository Name

Edit `.github/workflows/docker-publish.yml` and update the `DOCKER_IMAGE_NAME`:

```yaml
env:
  DOCKER_IMAGE_NAME: YOUR_DOCKERHUB_USERNAME/kea-gui-reservations
```

### Step 2: Add Docker Hub Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:

   **Secret 1: DOCKER_USERNAME**
   - Name: `DOCKER_USERNAME`
   - Value: Your Docker Hub username

   **Secret 2: DOCKER_PASSWORD**
   - Name: `DOCKER_PASSWORD`
   - Value: Your Docker Hub access token (NOT your password!)

#### How to Create a Docker Hub Access Token:

1. Log in to [Docker Hub](https://hub.docker.com/)
2. Click your username → **Account Settings**
3. Go to **Security** → **Access Tokens**
4. Click **New Access Token**
5. Give it a name (e.g., "GitHub Actions")
6. Set permissions to **Read, Write, Delete**
7. Click **Generate**
8. **Copy the token** (you won't be able to see it again!)
9. Use this token as the `DOCKER_PASSWORD` secret value

### Step 3: Create a Version Tag

When you're ready to publish a new version:

```bash
# Commit your changes
git add .
git commit -m "Release version 1.0.0"

# Create and push a version tag
git tag v1.0.0
git push origin v1.0.0
```

Or create a tag for a specific commit:

```bash
git tag v1.0.0 abc1234
git push origin v1.0.0
```

### Step 4: Watch the Build

1. Go to your GitHub repository
2. Click the **Actions** tab
3. You'll see the workflow running
4. Wait for it to complete (usually 2-5 minutes)

### Step 5: Verify the Image

Once the workflow completes:

```bash
# Pull the image
docker pull awkto/kea-gui-reservations:1.0.0

# Or pull the latest
docker pull awkto/kea-gui-reservations:latest
```

## What the Workflow Does

When you push a tag like `v1.0.0`, the workflow:

1. ✅ Checks out your code
2. ✅ Extracts the version number (removes the 'v' prefix)
3. ✅ Builds a Docker image for **multiple platforms** (amd64 and arm64)
4. ✅ Pushes the image with **two tags**:
   - `awkto/kea-gui-reservations:1.0.0` (version-specific)
   - `awkto/kea-gui-reservations:latest` (always points to newest)
5. ✅ Creates a **GitHub Release** with the tag
6. ✅ Adds release notes with Docker pull/run commands

## Version Tag Format

Use semantic versioning tags:
- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.1.1` - Patch release (bug fixes)
- `v2.0.0-beta.1` - Pre-release

The `v` prefix is required!

## Multi-Platform Support

The workflow builds for:
- `linux/amd64` (Intel/AMD x86_64)
- `linux/arm64` (ARM 64-bit, e.g., Raspberry Pi 4, Apple Silicon)

This means the same image works on most systems!

## Caching

The workflow uses GitHub Actions cache to speed up builds:
- First build: ~3-5 minutes
- Subsequent builds: ~1-2 minutes

## Troubleshooting

### Error: "denied: requested access to the resource is denied"

- Check that `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets are set correctly
- Verify the Docker Hub repository exists
- Make sure the access token has **Write** permissions

### Error: "repository name must be lowercase"

- Update `DOCKER_IMAGE_NAME` to use lowercase only

### Workflow doesn't trigger

- Make sure you pushed the tag: `git push origin v1.0.0`
- Tag must start with `v` followed by a version number

### Want to build on every push?

Change the trigger in `.github/workflows/docker-publish.yml`:

```yaml
on:
  push:
    branches:
      - main
    tags:
      - 'v*.*.*'
```

## Manual Trigger (Optional)

To allow manual workflow runs, add:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:  # Adds "Run workflow" button in GitHub
```

## Example Release Process

```bash
# 1. Make your changes
git add .
git commit -m "Add new feature"

# 2. Push to main
git push origin main

# 3. When ready to release, create a tag
git tag v1.0.0
git push origin v1.0.0

# 4. Go to GitHub Actions and watch the build

# 5. Once complete, users can pull:
docker pull awkto/kea-gui-reservations:latest
```

## Using the Published Image

Once published, users can use your image:

```bash
# Pull the image
docker pull awkto/kea-gui-reservations:latest

# Run with custom config
docker run -d \
  --name kea-gui \
  -p 5000:5000 \
  -v $(pwd)/config.yaml:/app/config/config.yaml:ro \
  awkto/kea-gui-reservations:latest

# Or use docker-compose
docker-compose up -d
```

## Benefits

✅ Automated builds - no manual Docker commands needed  
✅ Multi-platform support - works on x86_64 and ARM  
✅ Version tracking - every release is tagged  
✅ GitHub Releases - automatic changelog  
✅ Fast builds - uses layer caching  
✅ Latest tag - always points to newest version  

---

Need help? Check the [GitHub Actions documentation](https://docs.github.com/en/actions) or open an issue!
