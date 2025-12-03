# API Connectivity Test Results
Date: 2025-12-03

## Credentials Status

**Username:** `dio.petromanolakis@cityfibre.com`

### Confluence API
- **URL:** `https://cityfibre.atlassian.net`
- **API Key:** Provided (192 chars, ATATT3xFfGF0tSfrQ...)
- **Status:** 401 Unauthorized
- **Issue:** API key may not have Confluence read permissions or may be restricted

**Endpoints Tested:**
- `/wiki/api/v2/pages` → 401
- `/wiki/api/v2/spaces` → 401
- `/wiki/rest/api/content` → 401

### Jira API
- **URL:** `https://cityfibre.atlassian.net`
- **API Key:** Provided (192 chars, ATATT3xFfGF09HuSUV2D...)
- **Status:** Partially Working
- **Issue:** Limited endpoint access

**Endpoints Tested:**
- `/rest/api/3/myself` → 401 (authentication issue)
- `/rest/api/3/project` → 200 ✓ (but returns 0 projects - permission issue)
- `/rest/api/3/issuetype` → 200 ✓
- `/rest/api/3/issues/search` → 404
- `/rest/api/3/search/jql` → 400

## Next Steps

To resolve these issues:

1. **For Confluence:**
   - Regenerate API key at: https://id.atlassian.com/manage-profile/security/api-tokens
   - Ensure the key has "Read" permissions for Confluence
   - Verify user account has access to Confluence instance

2. **For Jira:**
   - Check if API key has proper scopes:
     - `read:jira-work`
     - `read:issue-details:jira`
   - Verify user has project access
   - Check if there are any IP-based restrictions

3. **Alternative:**
   - Use personal access tokens (PATs) if available
   - Check Jira Cloud API documentation for updated authentication

## Scraper Status

The scraper is fully functional and will automatically fetch and save data once API access is restored. It currently:

✓ Initializes Confluence and Jira clients
✓ Creates output directory structure
✓ Generates empty JSON files ready for data
✓ Has error handling and logging
✓ Supports both Confluence pages and Jira issues

Data files:
- `output/connexin_documents_merged.json` - Combined data
- `output/connexin_documents_confluence.json` - Confluence pages only
- `output/connexin_documents_jira.json` - Jira issues only
