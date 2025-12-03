#!/usr/bin/env python3
"""
Confluence API Client (v1)
Handles fetching pages, content, and hierarchies from Confluence
"""

import logging
import os
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ConfluenceClient:
    def __init__(self, url: str, username: str, api_key: str):
        """Initialize Confluence client"""
        self.base_url = url.rstrip('/') if url else "https://cityfibre.atlassian.net"
        self.username = username
        self.api_key = api_key
        self.auth = HTTPBasicAuth(username, api_key)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        logger.info(f"Confluence client initialized for {self.base_url}")

    def get_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single page by ID"""
        try:
            url = f"{self.base_url}/wiki/api/v2/pages/{page_id}"
            params = {
                "body-format": "storage"
            }
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            page = response.json()
            return page
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {str(e)}")
            return None

    def get_page_children(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all child pages of a given page"""
        try:
            url = f"{self.base_url}/wiki/api/v2/pages/{page_id}/children"
            params = {
                "limit": 250,
                "body-format": "storage"
            }
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('results', [])
        except Exception as e:
            logger.error(f"Error fetching children of page {page_id}: {str(e)}")
            return []

    def extract_text_from_html(self, html: str) -> str:
        """Extract clean text from Confluence HTML storage format"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "ac:macro"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML: {str(e)}")
            return html

    def get_page_hierarchy(self, root_page_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Recursively fetch a page and all its children"""
        pages = []
        
        def _fetch_recursive(page_id: str, depth: int = 0):
            if depth > max_depth:
                return
            
            try:
                page = self.get_page_by_id(page_id)
                if not page:
                    return
                
                # Extract content from v2 API response
                body_content = ""
                if 'body' in page and 'storage' in page['body']:
                    body_content = page['body']['storage'].get('value', '')
                elif 'body' in page and 'view' in page['body']:
                    body_content = page['body']['view'].get('value', '')
                
                page_data = {
                    'id': page['id'],
                    'title': page.get('title', ''),
                    'url': page.get('_links', {}).get('webui', f"{self.base_url}/wiki/spaces/*/pages/{page.get('id', '')}"),
                    'content': self.extract_text_from_html(body_content),
                    'space': page.get('spaceId', 'UNKNOWN'),
                    'created': page.get('createdAt', ''),
                    'modified': page.get('updatedAt', ''),
                    'depth': depth,
                    'source': 'confluence'
                }
                pages.append(page_data)
                logger.info(f"Fetched page: {page_data['title']} (ID: {page_id})")
                
                # Fetch children
                children = self.get_page_children(page_id)
                for child in children:
                    _fetch_recursive(child['id'], depth + 1)
            
            except Exception as e:
                logger.error(f"Error in recursive fetch for page {page_id}: {str(e)}")

        _fetch_recursive(root_page_id)
        return pages

    def search_pages(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for pages by text query"""
        try:
            url = f"{self.base_url}/wiki/api/v2/pages"
            params = {
                "title": query,
                "limit": limit,
                "body-format": "storage"
            }
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            results = response.json()
            
            pages = []
            for result in results.get('results', []):
                pages.append({
                    'id': result['id'],
                    'title': result.get('title', ''),
                    'url': result.get('_links', {}).get('webui', ''),
                    'excerpt': result.get('body', {}).get('view', {}).get('value', '')[:200],
                    'source': 'confluence'
                })
            
            return pages
        except Exception as e:
            logger.error(f"Error searching pages: {str(e)}")
            return []

    def get_recent_pages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent pages from Confluence"""
        try:
            url = f"{self.base_url}/wiki/api/v2/pages"
            params = {
                "limit": limit,
                "body-format": "storage"
            }
            response = requests.get(
                url,
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            results = response.json()
            
            pages = []
            for result in results.get('results', []):
                # Extract content from v2 API response
                body_content = ""
                if 'body' in result and 'storage' in result['body']:
                    body_content = result['body']['storage'].get('value', '')
                elif 'body' in result and 'view' in result['body']:
                    body_content = result['body']['view'].get('value', '')
                
                page_data = {
                    'id': result['id'],
                    'title': result.get('title', ''),
                    'url': result.get('_links', {}).get('webui', f"{self.base_url}/wiki/spaces/*/pages/{result.get('id', '')}"),
                    'content': self.extract_text_from_html(body_content),
                    'space': result.get('spaceId', 'UNKNOWN'),
                    'created': result.get('createdAt', ''),
                    'modified': result.get('updatedAt', ''),
                    'depth': 0,
                    'source': 'confluence'
                }
                pages.append(page_data)
                logger.info(f"Fetched recent page: {page_data['title']}")
            
            return pages
        except Exception as e:
            logger.error(f"Error fetching recent pages: {str(e)}")
            return []