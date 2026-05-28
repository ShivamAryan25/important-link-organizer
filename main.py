import os
import json
import requests
from firecrawl import Firecrawl
from google import genai


# =========================
# CONFIG
# =========================
NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]
FIRECRAWL_API_KEY = os.environ["FIRECRAWL_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

ALLOWED_TAGS = [
    "AI Tool",
    "GitHub Repo",
    "Documentation",
    "Roadmap",
    "Tutorial",
    "Article",
    "Video",
    "Course",
    "Frontend",
    "Backend",
    "DevOps",
    "Cloud",
    "Database",
    "Productivity",
    "Other",
]


# =========================
# NOTION HEADERS
# =========================
def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


# =========================
# GET PAGES FROM NOTION
# =========================
def get_pages():
    url = f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}/query"

    response = requests.post(
        url,
        headers=notion_headers(),
    )

    response.raise_for_status()

    data = response.json()

    return data["results"]


# =========================
# FIRECRAWL SUMMARY
# =========================
def get_firecrawl_summary(url):
    app = Firecrawl(api_key=FIRECRAWL_API_KEY)

    data = app.scrape(
        url,
        only_main_content=False,
        max_age=172800000,
        parsers=["pdf"],
        formats=["summary"]
    )

    summary = ""

    if isinstance(data, dict):

        if "summary" in data:
            summary = data["summary"]

        elif "data" in data:
            summary = data["data"].get("summary", "")

    else:
        summary = getattr(data, "summary", "")

    return summary


# =========================
# GEMINI PROCESSING
# =========================
def process_with_gemini(summary):

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are organizing saved internet resources.

Return ONLY valid JSON.

Format:
{{
  "what_for": "short description",
  "tags": ["tag1", "tag2"]
}}

Allowed tags:
{ALLOWED_TAGS}

Rules:
- Keep what_for within 1 sentence.
- Keep it concise.
- Choose only from allowed tags.
- Use maximum 3 tags.
- Return ONLY JSON.
- No markdown.

CONTENT:
{summary}
"""

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )

    text = response.text.strip()

    # Extract JSON safely
    start = text.find("{")
    end = text.rfind("}")

    clean_json = text[start:end+1]

    return json.loads(clean_json)


# =========================
# UPDATE NOTION PAGE
# =========================
def update_page(page_id, what_for, tags):

    url = f"{NOTION_BASE_URL}/pages/{page_id}"

    payload = {
        "properties": {

            "What for": {
                "rich_text": [
                    {
                        "text": {
                            "content": what_for
                        }
                    }
                ]
            },

            "Type": {
                "multi_select": [
                    {"name": tag} for tag in tags
                ]
            }

        }
    }

    response = requests.patch(
        url,
        headers=notion_headers(),
        json=payload,
    )

    response.raise_for_status()


# =========================
# MAIN WORKFLOW
# =========================
def run():

    pages = get_pages()

    print(f"Found {len(pages)} pages")

    for page in pages:

        try:

            properties = page["properties"]

            # =========================
            # GET LINK
            # =========================
            link = properties["Link"]["url"]

            if not link:
                continue

            # =========================
            # SKIP IF ALREADY PROCESSED
            # =========================
            existing_text = ""

            if properties["What for"]["rich_text"]:
                existing_text = properties["What for"]["rich_text"][0]["plain_text"]

            if existing_text:
                print("Skipping already processed row")
                continue

            print("\n=========================")
            print("Processing:", link)

            # =========================
            # FIRECRAWL
            # =========================
            summary = get_firecrawl_summary(link)

            if not summary:
                print("No summary returned")
                continue

            print("Firecrawl summary fetched")

            # =========================
            # GEMINI
            # =========================
            ai_data = process_with_gemini(summary)

            what_for = ai_data["what_for"]
            tags = ai_data["tags"]

            print("AI Description:", what_for)
            print("Tags:", tags)

            # =========================
            # UPDATE NOTION
            # =========================
            update_page(
                page["id"],
                what_for,
                tags,
            )

            print("Notion updated successfully")

        except Exception as e:
            print("\nERROR:", e)


# =========================
# RUN
# =========================
run()
