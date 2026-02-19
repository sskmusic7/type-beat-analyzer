# 🔒 Security Notice - API Keys Exposed

## ⚠️ Action Required

**ACRCloud API keys were exposed in commit 3069411** and have been detected by GitGuardian.

### What Happened
- File `ACRCLOUD_PROJECT_KEYS.md` contained actual API credentials
- These were committed to the public repository
- GitGuardian detected: `ACRCLOUD_ACCESS_SECRET=n49m5IoqZQNmxj5gRsIYptZUFJ1kQ8G9`

### Immediate Actions Taken ✅
1. ✅ Removed actual keys from `ACRCLOUD_PROJECT_KEYS.md`
2. ✅ Added file to `.gitignore` to prevent future commits
3. ✅ Removed file from git cache

### Required Actions (YOU MUST DO)

#### 1. Rotate Your ACRCloud API Keys 🔄
**URGENT**: Since these keys were exposed publicly, you MUST rotate them:

1. Go to: https://console.acrcloud.com
2. Navigate to your project settings
3. **Revoke/Delete** the old keys:
   - `ACRCLOUD_ACCESS_KEY=rPuhqHhPN7idRMQX`
   - `ACRCLOUD_ACCESS_SECRET=n49m5IoqZQNmxj5gRsIYptZUFJ1kQ8G9`
4. Generate **new keys**
5. Update your `.env` file with the new keys

#### 2. Check for Other Exposed Secrets 🔍
Review these files for any other secrets:
- `.env` files (should be gitignored)
- Any `*_keys.md` or `*_secrets.md` files
- Configuration files with hardcoded credentials

#### 3. Remove from Git History (Optional but Recommended) 📜
The keys are still in git history. To fully remove them:

```bash
# Option 1: Use git filter-branch (advanced)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch ACRCLOUD_PROJECT_KEYS.md" \
  --prune-empty --tag-name-filter cat -- --all

# Option 2: Use BFG Repo-Cleaner (easier)
# Download BFG: https://rtyley.github.io/bfg-repo-cleaner/
bfg --delete-files ACRCLOUD_PROJECT_KEYS.md
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# After either method, force push (WARNING: rewrites history)
git push origin --force --all
```

⚠️ **Warning**: Rewriting git history will require force push and may affect collaborators.

### Prevention for Future 🔐

1. **Never commit secrets** to git
2. **Always use `.env` files** (already in `.gitignore`)
3. **Use placeholders** in documentation:
   - ❌ `ACRCLOUD_KEY=abc123xyz`
   - ✅ `ACRCLOUD_KEY=YOUR_KEY_HERE`
4. **Use secret scanning tools**:
   - GitGuardian (already set up ✅)
   - GitHub Secret Scanning
   - Pre-commit hooks

### Current Status
- ✅ Secrets removed from current code
- ✅ `.gitignore` updated
- ⚠️ Keys still in git history (needs rotation)
- ⚠️ Old keys still active (needs rotation)

---

**Last Updated**: February 19, 2026
**Status**: Fixed in code, keys need rotation
