#!/usr/bin/env python3
"""
Jira API Client (v3)
Handles fetching issues and data from Jira using REST API v3
"""

import logging
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, url: str, username: str, api_key: str):
        """Initialize Jira client"""
        self.base_url = url.rstrip('/') if url else "https://cityfibre.atlassian.net"
        self.username = username
        self.api_key = api_key
        self.auth = HTTPBasicAuth(username, api_key)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        logger.info(f"Jira client initialized for {self.base_url}")

    def search_issues(self, search_query: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search for issues by fetching from projects and filtering"""
        issues = []
        try:
            # Get all projects
            response = requests.get(
                f"{self.base_url}/rest/api/3/project",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            projects = response.json()
            
            logger.info(f"Found {len(projects)} projects to search")
            
            # If we have a search query, search through more projects
            max_projects = 20 if search_query else 10
            
            # Search through projects for matching issues
            for project in projects[:max_projects]:
                try:
                    proj_key = project['key']
                    # Try to get issues from this project
                    response = requests.get(
                        f"{self.base_url}/rest/api/3/projects/{proj_key}/issues",
                        params={"maxResults": limit},
                        auth=self.auth,
                        headers=self.headers
                    )
                    
                    # If that endpoint doesn't work, try to get issues by browsing
                    if response.status_code != 200:
                        continue
                    
                    project_issues = response.json().get('issues', [])
                    
                    for issue in project_issues:
                        if len(issues) >= limit:
                            break
                        
                        # Filter by search query if provided
                        if search_query:
                            title = issue.get('fields', {}).get('summary', '').lower()
                            desc = issue.get('fields', {}).get('description', '')
                            if isinstance(desc, dict):
                                desc = self._extract_adf_text(desc).lower()
                            else:
                                desc = str(desc).lower()
                            
                            if search_query.lower() not in title and search_query.lower() not in desc:
                                continue
                        
                        issue_data = {
                            'key': issue['key'],
                            'id': issue['id'],
                            'title': issue.get('fields', {}).get('summary', ''),
                            'description': issue.get('fields', {}).get('description', ''),
                            'status': issue.get('fields', {}).get('status', {}).get('name', ''),
                            'project': issue.get('fields', {}).get('project', {}).get('key', ''),
                            'issue_type': issue.get('fields', {}).get('issuetype', {}).get('name', ''),
                            'created': issue.get('fields', {}).get('created', ''),
                            'updated': issue.get('fields', {}).get('updated', ''),
                            'assignee': issue.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned'),
                            'url': f"{self.base_url}/browse/{issue['key']}",
                            'content': self._extract_issue_content(issue),
                            'source': 'jira'
                        }
                        issues.append(issue_data)
                        logger.info(f"Fetched issue: {issue['key']} - {issue_data['title']}")
                
                except Exception as e:
                    logger.debug(f"Error fetching issues from project {proj_key}: {str(e)}")
                    continue
            
            return issues
        except Exception as e:
            logger.error(f"Error searching issues: {str(e)}")
            return []

    def get_issue_by_key(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Fetch a single issue by key"""
        try:
            url = f"{self.base_url}/rest/api/3/issues/{issue_key}"
            response = requests.get(
                url,
                auth=self.auth,
                headers=self.headers,
                params={"expand": "changelog"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {str(e)}")
            return None

    def _extract_issue_content(self, issue: Dict[str, Any]) -> str:
        """Extract and combine content from an issue"""
        content_parts = []
        
        fields = issue.get('fields', {})
        
        # Add summary
        if summary := fields.get('summary'):
            content_parts.append(f"Summary: {summary}")
        
        # Add description
        if description := fields.get('description'):
            if isinstance(description, dict):
                # Handle ADF (Atlassian Document Format)
                content_parts.append(self._extract_adf_text(description))
            else:
                content_parts.append(f"Description: {description}")
        
        # Add comments if available
        if changelog := issue.get('changelog', {}).get('histories', []):
            for history in changelog[:5]:  # Limit to recent 5
                if history.get('items'):
                    content_parts.append(f"Update: {history.get('created', '')}")
        
        return ' '.join(content_parts)

    def _extract_adf_text(self, adf_doc: Dict[str, Any]) -> str:
        """Extract text from Atlassian Document Format"""
        text_parts = []
        
        def extract_from_block(block):
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                if 'content' in block:
                    for item in block['content']:
                        extract_from_block(item)
        
        if content := adf_doc.get('content', []):
            for item in content:
                extract_from_block(item)
        
        return ' '.join(text_parts)

    def get_lit_issues(self) -> List[Dict[str, Any]]:
        """Fetch all issues related to LIT project"""
        # First try to find LIT-specific issues
        lit_issues = self.search_issues("lit", limit=30)
        # If none found, fetch some general recent issues
        if not lit_issues:
            logger.info("No LIT-specific issues found, fetching recent issues...")
            lit_issues = self.search_issues(None, limit=10)
        return lit_issues

    def get_connexin_issues(self) -> List[Dict[str, Any]]:
        """Fetch all issues related to Connexin"""
        # First try to find Connexin-specific issues
        connexin_issues = self.search_issues("connexin", limit=30)
        # If none found, fetch some general recent issues
        if not connexin_issues:
            logger.info("No Connexin-specific issues found, fetching recent issues...")
            connexin_issues = self.search_issues(None, limit=10)
        return connexin_issues
