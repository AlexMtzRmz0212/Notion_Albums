import os
from dotenv import load_dotenv
from notion_client import Client
from time import sleep

def fetch_all_pages(notion, db_id):
    pages = []
    response = notion.databases.query(database_id=db_id)
    pages.extend(response['results'])
    while response.get('has_more'):
        response = notion.databases.query(
            database_id=db_id,
            start_cursor=response['next_cursor']
        )
        pages.extend(response['results'])
    return pages

def get_used_alex_top_values(pages):
    used = set()
    for page in pages:
        prop = page['properties'].get('Alex Top')
        if prop and prop.get('select'):
            used.add(prop['select']['name'])
    return sorted(used)  # Sort for predictability

def chunked(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def reset_and_rebuild_select_options(notion, db_id, values):
    print("Step 1: Clearing all options...")
    notion.databases.update(
        database_id=db_id,
        properties={
            "Alex Top": {
                "select": {
                    "options": []
                }
            }
        }
    )
    print("All options cleared.")

    print(f"Step 2: Re-adding {len(values)} used options in chunks...")
    cumulative = []
    for idx, chunk in enumerate(chunked(values, 100), start=1):
        cumulative.extend({"name": val} for val in chunk)
        notion.databases.update(
            database_id=db_id,
            properties={
                "Alex Top": {
                    "select": {
                        "options": cumulative
                    }
                }
            }
        )
        print(f"✅ Chunk {idx} uploaded ({len(cumulative)} total)")
        sleep(0.2)  # Prevent possible rate limit

    print("🎉 Done! All used options restored.")

# --- Main ---
if __name__ == "__main__":
    print("This script is not woking properly due to Notion API rate limits.")
    # load_dotenv()
    # notion = Client(auth=os.getenv("API_KEY"))
    # db_id = os.getenv("DB_ID")

    # print("Fetching pages...")
    # pages = fetch_all_pages(notion, db_id)
    # used_values = get_used_alex_top_values(pages)

    # FIX Doesnt work due to rate limit of notion to just update 100 options at a time
    # print(f"Found {len(used_values)} used values.")
    # reset_and_rebuild_select_options(notion, db_id, used_values)
