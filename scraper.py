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
    # Try to fetch the root page hierarchy if available
    page_id = os.getenv('CONFLUENCE_PAGE_ID', None)
    if page_id:
        confluence_pages = confluence_client.get_page_hierarchy(page_id, max_depth=5)
    else:
        logger.info("Fetching recent Confluence pages...")
        confluence_pages = confluence_client.get_recent_pages(limit=20)
    
    # Format documents
    confluence_docs = [processor.format_confluence_document(page) for page in confluence_pages]
    logger.info(f"Processed {len(confluence_docs)} Confluence documents")
    
    # ========== JIRA ==========
    logger.info("Fetching Jira data...")
    
    # Fetch LIT issues
    lit_issues = jira_client.get_lit_issues()
    logger.info(f"Fetched {len(lit_issues)} LIT-related issues")
    
    # Fetch Connexin issues
    connexin_issues = jira_client.get_connexin_issues()
    logger.info(f"Fetched {len(connexin_issues)} Connexin-related issues")
    
    # Format documents
    jira_docs = [processor.format_jira_document(issue) for issue in (lit_issues + connexin_issues)]
    logger.info(f"Processed {len(jira_docs)} Jira documents")
    
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
