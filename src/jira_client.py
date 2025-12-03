#!/usr/bin/env python3
"""
Jira API Client
Handles fetching issues and data from Jira
"""

import logging
from typing import Dict, List, Any, Optional
from atlassian import Jira

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self, url: str, username: str, api_key: str):
        """Initialize Jira client"""
        self.url = url
        self.username = username
        self.api_key = api_key
        self.client = Jira(
            url=url,
            username=username,
            password=api_key,
            cloud=True
        )
        logger.info(f"Jira client initialized for {url}")

    def search_issues(self, jql: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Search for issues using JQL query"""
        try:
            results = self.client.jql(jql, start=0, limit=limit, expand='changelog')
            issues = []
            
            for issue in results.get('issues', []):
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
                    'url': f"{self.url}/browse/{issue['key']}",
                    'content': self._extract_issue_content(issue),
                    'source': 'jira'
                }
                issues.append(issue_data)
                logger.info(f"Fetched issue: {issue['key']} - {issue_data['title']}")
            
            return issues
        except Exception as e:
            logger.error(f"Error searching issues: {str(e)}")
            return []

    def get_issue_by_key(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Fetch a single issue by key"""
        try:
            issue = self.client.get_issue(issue_key, expand='changelog')
            return issue
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
        jql = 'textfields ~ "lit*" AND project in (CONNEXIN, IDA, CM)'
        return self.search_issues(jql, limit=200)

    def get_connexin_issues(self) -> List[Dict[str, Any]]:
        """Fetch all issues related to Connexin"""
        jql = 'textfields ~ "connexin*" OR project = CONNEXIN'
        return self.search_issues(jql, limit=200)
