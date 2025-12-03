#!/usr/bin/env python3
"""
Document Processor
Formats and processes documents from Confluence and Jira into unified JSON format
"""

import logging
import json
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and format documents for RAG pipeline"""
    
    @staticmethod
    def format_confluence_document(page: Dict[str, Any]) -> Dict[str, Any]:
        """Format a Confluence page into standard document format"""
        return {
            'id': page['id'],
            'title': page['title'],
            'content': page['content'],
            'source': page.get('url', ''),
            'source_type': 'confluence',
            'metadata': {
                'space': page.get('space', ''),
                'url': page.get('url', ''),
                'created': page.get('created', ''),
                'modified': page.get('modified', ''),
                'depth': page.get('depth', 0),
            },
            'document_type': 'wiki_page',
            'indexed_at': datetime.now().isoformat()
        }

    @staticmethod
    def format_jira_document(issue: Dict[str, Any]) -> Dict[str, Any]:
        """Format a Jira issue into standard document format"""
        return {
            'id': issue['id'],
            'title': f"{issue['key']}: {issue['title']}",
            'content': issue['content'],
            'source': issue.get('url', ''),
            'source_type': 'jira',
            'metadata': {
                'key': issue['key'],
                'project': issue.get('project', ''),
                'status': issue.get('status', ''),
                'issue_type': issue.get('issue_type', ''),
                'url': issue.get('url', ''),
                'created': issue.get('created', ''),
                'updated': issue.get('updated', ''),
                'assignee': issue.get('assignee', 'Unassigned'),
            },
            'document_type': 'issue',
            'indexed_at': datetime.now().isoformat()
        }

    @staticmethod
    def merge_documents(confluence_docs: List[Dict[str, Any]], 
                       jira_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge Confluence and Jira documents into a single list"""
        all_docs = confluence_docs + jira_docs
        logger.info(f"Merged {len(confluence_docs)} Confluence documents with {len(jira_docs)} Jira documents")
        return all_docs

    @staticmethod
    def save_to_json(documents: List[Dict[str, Any]], output_path: str) -> None:
        """Save documents to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(documents)} documents to {output_path}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")

    @staticmethod
    def load_from_json(file_path: str) -> List[Dict[str, Any]]:
        """Load documents from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Error loading from JSON: {str(e)}")
            return []
