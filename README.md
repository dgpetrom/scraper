# Connexin Scraper

Fetch and process data from Confluence and Jira for the CityFibre Knowledge Assistant RAG pipeline.

## Features

- 🌐 **Confluence Integration** - Fetch wiki pages and hierarchies from Confluence
- 🎯 **Jira Integration** - Search and fetch issues related to LIT and Connexin projects
- 📄 **Smart Processing** - Format documents for RAG pipeline consumption
- 💾 **JSON Export** - Save documents in unified JSON format
- 🔍 **Search Capability** - Search through downloaded documents
- 🚀 **CLI Interface** - Easy-to-use command-line interface

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` with your credentials:

```bash
CONFLUENCE_URL=https://cityfibre.atlassian.net
CONFLUENCE_USERNAME=your@email.com
CONFLUENCE_API_KEY=your-api-key

JIRA_URL=https://cityfibre.atlassian.net
JIRA_USERNAME=your@email.com
JIRA_API_KEY=your-api-key

OUTPUT_DIR=./output
```

## Usage

### Run Full Scraper

```bash
python scraper.py
```

### Using CLI

```bash
# Scrape with custom page and depth
python cli.py scrape --confluence-page-id 5345345542 --max-depth 5

# Search through documents
python cli.py search "your search query"
```

## Output

Documents are saved to `output/` directory:

- `connexin_documents_merged.json` - All documents combined
- `connexin_documents_confluence.json` - Confluence pages only
- `connexin_documents_jira.json` - Jira issues only

## Document Format

Each document follows this structure:

```json
{
  "id": "doc_id",
  "title": "Document Title",
  "content": "Full document content text",
  "source": "https://link-to-document",
  "source_type": "confluence|jira",
  "metadata": {
    "space": "CONFLUENCE_SPACE",
    "url": "https://...",
    "created": "2024-01-01T00:00:00",
    "modified": "2024-01-01T00:00:00"
  },
  "document_type": "wiki_page|issue",
  "indexed_at": "2024-01-01T00:00:00"
}
```

## Integration with RAG

To use the scraped documents with your RAG pipeline:

1. Copy the JSON file to your RAG project:
   ```bash
   cp output/connexin_documents_merged.json ../rag-servicenow/data/
   ```

2. Upload via the dashboard or API endpoint

## Logging

The scraper provides detailed logging. Check console output for progress and errors.

## Troubleshooting

- **Authentication Failed**: Verify API credentials in `.env`
- **No Documents Found**: Check Confluence page ID and Jira JQL queries
- **API Rate Limits**: The scraper handles rate limiting with retries

## Support

For issues or questions, check the logs and verify API credentials.
