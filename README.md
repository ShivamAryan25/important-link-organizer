# Important Link Organizer

Automatically summarizes and tags links saved to a Notion database, using Firecrawl for content extraction and Gemini for classification — so a links database stays organized without manual triage.

## How it works

1. **Fetch** — Queries a Notion database for every saved link.
2. **Skip processed rows** — If a page's `What for` field already has text, it's left alone.
3. **Scrape & summarize** — The link is sent to Firecrawl, which scrapes the page and returns a summary.
4. **Classify** — The summary is passed to Gemini (`gemini-3.1-flash-lite`), which returns a one-line description and up to 3 tags from a fixed list.
5. **Write back** — The description and tags are patched onto the corresponding Notion page.
6. A failure on any single page is logged and skipped — the script moves on to the next page.

## Tech stack

- Python 3.11
- Notion API
- Firecrawl (`firecrawl-py`) — scraping & summarization
- Google Gemini (`google-genai`) — classification
- GitHub Actions — scheduling

## Notion database schema

The target database needs these properties:

| Property   | Type         | Set by      |
|------------|--------------|-------------|
| `Link`     | URL          | you         |
| `What for` | Rich text    | script (AI) |
| `Type`     | Multi-select | script (AI) |

`Type` options must include the tags the script is allowed to choose from:
`AI Tool`, `GitHub Repo`, `Documentation`, `Roadmap`, `Tutorial`, `Article`, `Video`, `Course`, `Frontend`, `Backend`, `DevOps`, `Cloud`, `Database`, `Productivity`, `Other`

## Setup

1. Clone and install dependencies:
```bash
   git clone https://github.com/ShivamAryan25/Important-link-organizer.git
   cd Important-link-organizer
   pip install -r requirements.txt
```

2. Create a [Notion integration](https://www.notion.so/my-integrations), copy its token, and share your links database with it.

3. Set the required environment variables (below).

4. Run:
```bash
   python main.py
```

## Environment variables

| Variable             | Description                       |
|-----------------------|-----------------------------------|
| `NOTION_API_KEY`     | Notion integration token          |
| `NOTION_DATABASE_ID` | ID of the target Notion database  |
| `FIRECRAWL_API_KEY`  | Firecrawl API key                 |
| `GEMINI_API_KEY`     | Google Gemini API key             |

## Automation

`.github/workflows/python-app.yml` runs the script automatically on the schedule `*/55 * * * *`, and can also be triggered manually via `workflow_dispatch`.

To enable it on your own fork, add the four variables above as repository secrets:
`Settings → Secrets and variables → Actions → New repository secret`

## Project structure

```
.
├── main.py                           # fetch → summarize → classify → update
├── requirements.txt                  # firecrawl-py, google-genai, requests
└── .github/workflows/python-app.yml  # scheduled + manual automation
```
