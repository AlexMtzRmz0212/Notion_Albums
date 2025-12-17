import os
import time
from dotenv import load_dotenv
from notion_client import Client
from tqdm import tqdm
from utils import (
    clear_console,
    fetch_all_notion_pages
)


def parse_album_data(results):
    albums = []
    for result in results:
        title = result['properties']['Album']['title']
        name = title[0]['text']['content'] if title else 'Untitled'

        # Get rating
        select = result['properties']['Alex Top']['select']
        rating = int(select['name']) if select and select['name'] and select['name'].isdigit() else None

        # Get artist
        artist = result['properties']['Artist']['select']
        artist = artist['name'] if artist and artist['name'] else 'Unknown'

        # Get status
        status = result['properties']['Status']['status']
        status = status['name'] if status and status['name'] else 'Unknown'

        albums.append({
            'name': name,
            'Artist': artist,
            'Alex Top': rating,
            'Status': status
        })

    return albums



def ensure_unique_ranks(albums):
    """Ensure all albums have unique 'Alex Top' ranks by incrementing duplicates."""
    albums.sort(key=lambda x: x['Alex Top'])
    last_used = albums[0]['Alex Top'] if albums else 0
    for i in range(1, len(albums)):
        if albums[i]['Alex Top'] <= last_used:
            last_used += 1
            albums[i]['Alex Top'] = last_used
        else:
            last_used = albums[i]['Alex Top']
    return albums

def assign_default_ranks(albums, starting_rating):
    for i, album in enumerate(albums):
        album['Alex Top'] = starting_rating + i
    return albums

def format_ranks(albums, length):
    fmt = '{:0' + str(length) + '}'
    for album in albums:
        album['Alex Top'] = fmt.format(album['Alex Top'])
    return albums

def compact_ranks(albums, length):
    fmt = '{:0' + str(length) + '}'
    for i, album in enumerate(albums, 1):
        album['Alex Top'] = fmt.format(i)
    return albums

def main():

    load_dotenv()
    notion = Client(auth=os.getenv("API_KEY"))
    db_id = os.getenv("ALBUM_DB_ID")

    while True:
        try:
            clear_console()
            print("Retrieving from Notion...")
            start_time = time.time()

            all_results = fetch_all_notion_pages(notion, db_id)

            print(f"Fetched {len(all_results)} albums in {time.time() - start_time:.2f} seconds.")

            albums = parse_album_data(all_results)

            rankable = [a for a in albums if a['Status'] == 'Listened']

            rated = [a for a in rankable if a['Alex Top'] is not None]
            unrated = [a for a in rankable if a['Alex Top'] is None]

            rated = ensure_unique_ranks(rated)
            # Compute dynamic default rating (after fixing rated)
            highest_rating = max((a['Alex Top'] for a in rated), default=0)
            unrated = assign_default_ranks(unrated, highest_rating + 1)

            final_list = rated + unrated
            final_list.sort(key=lambda x: x['Alex Top'])

            # Choose formatting length
            max_val = final_list[-1]['Alex Top']
            fmt_length = 3 if max_val > 99 or len(final_list) > 99 else 2
            final_list = format_ranks(final_list, fmt_length)

            # Ask for sorting option
            while True:
                sorting_option = input("Choose sorting option (default/compact) [d/c]: ").lower()
                if sorting_option in ['default', 'd', 'compact', 'c']:
                    if sorting_option.startswith('c'):
                        final_list = compact_ranks(final_list, fmt_length)
                    break
                print("Please enter a valid option.")
            
            start_upload = time.time()  

            for _, item in tqdm(enumerate(final_list), total=len(final_list), desc="Updating Notion"):
                try:
                    page = next(
                        pg for pg in all_results
                        if pg['properties']['Album']['title']
                        and 'text' in pg['properties']['Album']['title'][0]
                        and pg['properties']['Album']['title'][0]['text']['content'] == item['name']
                    )
                    properties = {
                        "Album": {"title": [{"text": {"content": item['name']}}]},
                        "Alex Top": {"select": {"name": item['Alex Top']}}
                    }
                    notion.pages.update(page['id'], properties=properties)
                except Exception as e:
                    print(f"Failed to upload {item['name']}: {e}")

            print(f"Upload completed in {time.time() - start_upload:.2f} seconds.")

        except Exception as e:
            print(f"An error occurred: {e}")

        decision = input("Is the sorting finished? (y/n): ").strip().lower()
        if decision == "y":
            break

if __name__ == "__main__":
    main()