#!/usr/bin/env python3
"""
Main Scraper Script
Orchestrates fetching data from Confluence and Jira
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from src.confluence_client import ConfluenceClient
from src.jira_client import JiraClient
from src.document_processor import DocumentProcessor

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main scraper function"""
    
    # Initialize clients
    confluence_client = ConfluenceClient(
        url=os.getenv('CONFLUENCE_URL'),
        username=os.getenv('CONFLUENCE_USERNAME'),
        api_key=os.getenv('CONFLUENCE_API_KEY')
    )
    
    jira_client = JiraClient(
        url=os.getenv('JIRA_URL'),
        username=os.getenv('JIRA_USERNAME'),
        api_key=os.getenv('JIRA_API_KEY')
    )
    
    processor = DocumentProcessor()
    
    # Create output directory
    output_dir = Path(os.getenv('OUTPUT_DIR', './output'))
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Starting Connexin data scraping...")
    
    # ========== CONFLUENCE ==========
    logger.info("Fetching Confluence data...")
    
    confluence_pages = []
    # Fetch the LitWay Salesforce Migration Framework page (ID: 5345345542)
    page_id = os.getenv('CONFLUENCE_PAGE_ID', '5345345542')
    logger.info(f"Fetching page hierarchy from page ID: {page_id}")
    confluence_pages = confluence_client.get_page_hierarchy(page_id, max_depth=10)
    
    # Format documents
    confluence_docs = [processor.format_confluence_document(page) for page in confluence_pages]
    logger.info(f"Processed {len(confluence_docs)} Confluence documents")
    
    # ========== JIRA - Using Agile API ==========
    logger.info("Fetching Jira data via Agile API...")
    
    import json
    import requests
    from requests.auth import HTTPBasicAuth
    
    url = os.getenv('JIRA_URL')
    username = os.getenv('JIRA_USERNAME')
    api_key = os.getenv('JIRA_API_KEY')
    auth = HTTPBasicAuth(username, api_key)
    
    jira_issues = []
    try:
        # Fetch from Agile API (more reliable with limited permissions)
        response = requests.get(
            f'{url}/rest/agile/1.0/board',
            params={'maxResults': 50},
            auth=auth
        )
        
        if response.status_code == 200:
            boards = response.json().get('values', [])
            logger.info(f"Found {len(boards)} Jira boards")
            
            for board in boards:
                try:
                    board_response = requests.get(
                        f'{url}/rest/agile/1.0/board/{board["id"]}/issue',
                        params={'maxResults': 100},
                        auth=auth
                    )
                    if board_response.status_code == 200:
                        issues = board_response.json().get('issues', [])
                        jira_issues.extend(issues)
                except Exception as e:
                    logger.debug(f"Error fetching from board {board['name']}: {e}")
                    continue
            
            logger.info(f"Fetched {len(jira_issues)} total Jira issues")
            
            # Filter for relevant keywords
            keywords = ['LIT', 'Connexin', 'Salesforce', 'Migration', 'Framework', 'OLT', 'MAMLITFIBER']
            filtered_issues = []
            for issue in jira_issues:
                key = issue['key'].upper()
                summary = issue['fields']['summary'].upper()
                
                if any(keyword.upper() in key or keyword.upper() in summary for keyword in keywords):
                    filtered_issues.append(issue)
            
            logger.info(f"Filtered to {len(filtered_issues)} relevant issues")
            
            # Format documents
            jira_docs = []
            for issue in filtered_issues:
                doc = {
                    'id': issue['key'],
                    'title': issue['fields']['summary'],
                    'type': issue['fields']['issuetype']['name'],
                    'board': issue.get('board_name', 'Unknown'),
                    'content': f"{issue['key']}: {issue['fields']['summary']}",
                    'source': 'jira'
                }
                jira_docs.append(doc)
            
            logger.info(f"Processed {len(jira_docs)} Jira documents")
        else:
            logger.warning(f"Failed to fetch Jira boards: {response.status_code}")
            jira_docs = []
    except Exception as e:
        logger.error(f"Error fetching Jira data: {e}")
        jira_docs = []
    
    # ========== MERGE AND SAVE ==========
    all_documents = processor.merge_documents(confluence_docs, jira_docs)
    
    # Save merged documents
    merged_path = output_dir / 'connexin_documents_merged.json'
    processor.save_to_json(all_documents, str(merged_path))
    
    # Save separate files
    processor.save_to_json(confluence_docs, str(output_dir / 'connexin_documents_confluence.json'))
    processor.save_to_json(jira_docs, str(output_dir / 'connexin_documents_jira.json'))
    
    # Summary
    logger.info("=" * 60)
    logger.info("SCRAPING COMPLETE")
    logger.info(f"Total documents: {len(all_documents)}")
    logger.info(f"  - Confluence: {len(confluence_docs)}")
    logger.info(f"  - Jira: {len(jira_docs)}")
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
