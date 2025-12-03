#!/usr/bin/env python3
"""
CLI Interface for Connexin Scraper
"""

import typer
from pathlib import Path
import logging
from dotenv import load_dotenv
import os
from src.confluence_client import ConfluenceClient
from src.jira_client import JiraClient
from src.document_processor import DocumentProcessor
from rich.console import Console
from rich.progress import track

load_dotenv()

console = Console()
app = typer.Typer()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.command()
def scrape(
    confluence_page_id: str = typer.Option("5345345542", help="Confluence page ID to start scraping from"),
    max_depth: int = typer.Option(5, help="Maximum depth for page hierarchy"),
    output_dir: str = typer.Option("./output", help="Output directory for JSON files"),
    include_jira: bool = typer.Option(True, help="Include Jira issues in scraping")
):
    """Scrape Connexin data from Confluence and optionally Jira"""
    
    console.print("[bold cyan]🚀 Starting Connexin Scraper[/bold cyan]")
    
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    
    try:
        # Initialize clients
        confluence_client = ConfluenceClient(
            url=os.getenv('CONFLUENCE_URL'),
            username=os.getenv('CONFLUENCE_USERNAME'),
            api_key=os.getenv('CONFLUENCE_API_KEY')
        )
        
        processor = DocumentProcessor()
        all_documents = []
        
        # Fetch Confluence data
        console.print("\n[bold yellow]📄 Fetching Confluence pages...[/bold yellow]")
        confluence_pages = confluence_client.get_page_hierarchy(confluence_page_id, max_depth=max_depth)
        confluence_docs = [processor.format_confluence_document(page) for page in confluence_pages]
        all_documents.extend(confluence_docs)
        console.print(f"✓ Processed {len(confluence_docs)} Confluence documents")
        
        # Fetch Jira data if requested
        if include_jira:
            console.print("\n[bold yellow]🎯 Fetching Jira issues...[/bold yellow]")
            jira_client = JiraClient(
                url=os.getenv('JIRA_URL'),
                username=os.getenv('JIRA_USERNAME'),
                api_key=os.getenv('JIRA_API_KEY')
            )
            
            lit_issues = jira_client.get_lit_issues()
            connexin_issues = jira_client.get_connexin_issues()
            
            jira_docs = [processor.format_jira_document(issue) for issue in (lit_issues + connexin_issues)]
            all_documents.extend(jira_docs)
            console.print(f"✓ Processed {len(jira_docs)} Jira documents")
        
        # Save files
        console.print("\n[bold yellow]💾 Saving documents...[/bold yellow]")
        merged_path = Path(output_dir) / 'connexin_documents_merged.json'
        processor.save_to_json(all_documents, str(merged_path))
        
        # Summary
        console.print("\n[bold green]✅ Scraping Complete![/bold green]")
        console.print(f"\nTotal documents: {len(all_documents)}")
        console.print(f"Output: {merged_path.absolute()}")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Error: {str(e)}[/bold red]")
        raise typer.Exit(code=1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    json_file: str = typer.Option("./output/connexin_documents_merged.json", help="JSON file to search in")
):
    """Search through scraped documents"""
    
    processor = DocumentProcessor()
    documents = processor.load_from_json(json_file)
    
    if not documents:
        console.print("[red]No documents found[/red]")
        return
    
    query_lower = query.lower()
    results = [d for d in documents if query_lower in d.get('title', '').lower() or query_lower in d.get('content', '').lower()]
    
    console.print(f"\n[bold]Found {len(results)} results:[/bold]\n")
    for doc in results[:10]:  # Show top 10
        console.print(f"📝 {doc['title']}")
        console.print(f"   Source: {doc['source_type']}")
        console.print(f"   URL: {doc['source']}\n")


if __name__ == '__main__':
    app()
