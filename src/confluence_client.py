#!/usr/bin/env python3
"""
Confluence API Client
Handles fetching pages, content, and hierarchies from Confluence
"""

import logging
import os
from typing import Dict, List, Any, Optional
from atlassian import Confluence
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ConfluenceClient:
    def __init__(self, url: str, username: str, api_key: str):
        """Initialize Confluence client"""
        self.url = url
        self.username = username
        self.api_key = api_key
        self.client = Confluence(
            url=url,
            username=username,
            password=api_key,
            cloud=True
        )
        logger.info(f"Confluence client initialized for {url}")

    def get_page_by_id(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single page by ID"""
        try:
            page = self.client.get_page_by_id(page_id, expand='body.storage,metadata')
            return page
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {str(e)}")
            return None

    def get_page_children(self, page_id: str) -> List[Dict[str, Any]]:
        """Get all child pages of a given page"""
        try:
            children = self.client.get_page_child_by_type(page_id, type='page', expand='body.storage')
            return children if children else []
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
                
                # Extract content
                page_data = {
                    'id': page['id'],
                    'title': page['title'],
                    'url': page['_links']['webui'] if '_links' in page else f"{self.url}/wiki/spaces/{page.get('space', {}).get('key', '')}/pages/{page['id']}",
                    'content': self.extract_text_from_html(page.get('body', {}).get('storage', {}).get('value', '')),
                    'space': page.get('space', {}).get('key', 'UNKNOWN'),
                    'created': page.get('metadata', {}).get('created', ''),
                    'modified': page.get('metadata', {}).get('updated', ''),
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
            results = self.client.search_by_text(query, limit=limit)
            pages = []
            for result in results.get('results', []):
                if result['type'] == 'page':
                    pages.append({
                        'id': result['id'],
                        'title': result.get('title', ''),
                        'url': self.url + result.get('url', ''),
                        'excerpt': result.get('excerpt', ''),
                        'source': 'confluence'
                    })
            return pages
        except Exception as e:
            logger.error(f"Error searching pages: {str(e)}")
            return []
