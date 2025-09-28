# GitHub Pages Setup Guide

## Overview

This guide explains how to properly configure GitHub Pages for the Trading System documentation, including troubleshooting common permission issues.

## Prerequisites

1. **Repository Access**: You must have admin/write access to the repository
2. **GitHub Pages Enabled**: Pages must be enabled in repository settings
3. **Correct Permissions**: Workflow must have proper permissions

## Step-by-Step Setup

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **Pages** section (left sidebar)
4. Under **Source**, select **GitHub Actions**
5. Click **Save**

### 2. Configure Repository Permissions

1. In repository **Settings**
2. Go to **Actions** → **General**
3. Scroll to **Workflow permissions**
4. Select **Read and write permissions**
5. Check **Allow GitHub Actions to create and approve pull requests**
6. Click **Save**

### 3. Verify Workflow Configuration

The workflow should have these permissions:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### 4. Deploy Documentation

1. Push changes to `main` branch
2. Go to **Actions** tab
3. Find the **Documentation** workflow
4. Click on the latest run
5. Monitor the deployment progress

## Troubleshooting

### Error: Permission Denied

**Error**: `Permission to nishantnayar/Trading-System.git denied to github-actions[bot]`

**Solutions**:

1. **Check Repository Permissions**:
   - Go to Settings → Actions → General
   - Ensure "Read and write permissions" is selected
   - Save changes

2. **Verify Workflow Permissions**:
   ```yaml
   permissions:
     contents: read
     pages: write
     id-token: write
   ```

3. **Check GitHub Pages Source**:
   - Go to Settings → Pages
   - Ensure source is set to "GitHub Actions"

### Error: 403 Forbidden

**Error**: `The requested URL returned error: 403`

**Solutions**:

1. **Regenerate Token** (if using personal access token):
   - Go to Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` and `workflow` permissions
   - Update repository secrets

2. **Use Built-in GITHUB_TOKEN** (recommended):
   - Remove custom token from workflow
   - Use `${{ secrets.GITHUB_TOKEN }}` (automatic)

### Error: Pages Not Found

**Error**: 404 when accessing GitHub Pages URL

**Solutions**:

1. **Check Deployment Status**:
   - Go to Actions tab
   - Look for "Deploy to GitHub Pages" job
   - Ensure it completed successfully

2. **Verify Pages Settings**:
   - Go to Settings → Pages
   - Check if Pages is enabled
   - Verify source is "GitHub Actions"

3. **Check Custom Domain** (if used):
   - Ensure CNAME file is correct
   - Verify DNS settings

## Alternative Deployment Methods

### Method 1: Manual Deployment

If automatic deployment fails, you can deploy manually:

```bash
# Build documentation
mkdocs build

# Deploy using gh-pages branch
git checkout --orphan gh-pages
git rm -rf .
cp -r site/* .
git add .
git commit -m "Deploy documentation"
git push origin gh-pages
```

### Method 2: Personal Access Token

If built-in token doesn't work:

1. **Create Personal Access Token**:
   - Go to Settings → Developer settings → Personal access tokens
   - Generate new token with `repo` and `workflow` permissions

2. **Add to Repository Secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Add new secret: `GH_PAGES_TOKEN`
   - Paste your personal access token

3. **Update Workflow**:
   ```yaml
   - name: Deploy to GitHub Pages
     uses: peaceiris/actions-gh-pages@v4
     with:
       github_token: ${{ secrets.GH_PAGES_TOKEN }}
       publish_dir: ./site
   ```

## Verification

### Check Deployment

1. **Visit GitHub Pages URL**:
   - `https://nishantnayar.github.io/trading-system`
   - Should show your documentation

2. **Check Actions Logs**:
   - Go to Actions tab
   - Look for successful deployment
   - Check for any error messages

3. **Verify Content**:
   - All pages should load correctly
   - Navigation should work
   - Images and assets should display

## Best Practices

### 1. Use Modern GitHub Actions

```yaml
# ✅ Recommended (modern)
- uses: actions/configure-pages@v4
- uses: actions/upload-pages-artifact@v3
- uses: actions/deploy-pages@v4

# ❌ Avoid (deprecated)
- uses: peaceiris/actions-gh-pages@v4
```

### 2. Set Proper Permissions

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### 3. Use Conditional Deployment

```yaml
- name: Deploy to GitHub Pages
  if: github.ref == 'refs/heads/main'
  uses: actions/deploy-pages@v4
```

### 4. Monitor Deployments

- Check Actions tab regularly
- Set up notifications for failed deployments
- Monitor repository settings for changes

## Common Issues and Solutions

### Issue: Workflow Runs But Pages Don't Update

**Solution**:
1. Check if Pages source is set to "GitHub Actions"
2. Verify workflow completed successfully
3. Wait 5-10 minutes for propagation
4. Clear browser cache

### Issue: Custom Domain Not Working

**Solution**:
1. Add CNAME file to repository root
2. Configure DNS settings with your domain provider
3. Wait for DNS propagation (up to 24 hours)

### Issue: Build Fails

**Solution**:
1. Check MkDocs configuration
2. Verify all dependencies are installed
3. Test build locally: `mkdocs build`
4. Check for broken links

## Monitoring and Maintenance

### Regular Checks

1. **Weekly**: Check Actions tab for failed runs
2. **Monthly**: Verify Pages are accessible
3. **After Changes**: Test documentation locally

### Automated Monitoring

Set up notifications for:
- Failed workflow runs
- Deployment errors
- Broken links in documentation

## Support

### GitHub Documentation

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Permissions](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#permissions)

### Project Resources

- [CI/CD Pipeline](CI_CD_PIPELINE.md)
- [CI/CD Troubleshooting](CI_CD_TROUBLESHOOTING.md)
- [Testing Strategy](TESTING_STRATEGY.md)

---

**Note**: This setup ensures reliable, automated documentation deployment with proper permissions and modern GitHub Actions practices.
