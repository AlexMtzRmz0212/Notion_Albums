import time
from notion_client import Client
from tqdm import tqdm
import os
import subprocess
from dotenv import load_dotenv
from io import StringIO


# region 1: Decrypt the .env.enc file using the encryption key stored in the environment variable
def decrypt_env_file():
    key = os.getenv('ENCRYPTION_KEY')
    if not key:
        raise Exception("ENCRYPTION_KEY is not set!")

    # Step 2: Use OpenSSL to decrypt the .env.enc file with PBKDF2 and iter
    try:
        result = subprocess.run(
            ['openssl', 'aes-256-cbc', '-d', '-in', '.env.enc', '-pass', f'pass:{key}', '-pbkdf2', '-iter', '100000'],
            capture_output=True, 
            text=True,
            check=True  
        )
    
    except FileNotFoundError:
        raise RuntimeError("OpenSSL is not installed or not found in PATH.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Decryption failed. Check if the key is correct and `.env.enc` is valid.\nDetails: {e.stderr.strip()}")

    return StringIO(result.stdout)

# Step 3: Load the decrypted environment variables
def load_secrets():
    try:
        dotenv_loaded = load_dotenv(stream=decrypt_env_file())
        if not dotenv_loaded:
            raise RuntimeError("Failed to load environment variables from decrypted file.")
    except Exception as e:
        raise RuntimeError(f"Error loading secrets: {e}")

    # Check that required keys exist
    required_vars = ['API_KEY', 'DB_ID']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

# Step 4: Load secrets and use them
load_secrets()
# endregion

api_key = os.getenv("API_KEY")

notion = Client(auth=api_key)
DBID = os.getenv("DB_ID")

defaultRating = 999
all_results = []

while True:
    try:
        os.system('cls')
        startTime = time.time()
        #Get all the database, sorted ascendingly through Alex Top property
        print("Retrieving from Notion...")
        Response = notion.databases.query(database_id=DBID)#,sorts=[{"property": "Alex Top","direction": "ascending"}])
        all_results.extend(Response['results'])
        while Response.get('has_more', False):
            # Fetch next page of results
            Response = notion.databases.query(database_id=DBID, start_cursor=Response['next_cursor'])
            all_results.extend(Response['results'])
        EndTime = time.time()
        print("Albums retrieved")
        Duration = EndTime - startTime
        print(f"The Albums Fetching took {Duration} seconds to complete")
        albums = []
        for result in all_results:
            # Check if 'title' list is not empty and then access to the name
            NameResult = result['properties']['Album']['title'][0]['text']['content'] if result['properties']['Album']['title'] else 'Untitled'

            # Check if 'select' is not None and then access to the Top
            TopResult = result['properties']['Alex Top']['select']['name'] if result['properties']['Alex Top']['select'] else None

            # Convert TopResult to int if it's not None, otherwise, leave it as None
            albums.append({'name': NameResult, 'Alex Top': int(TopResult) if TopResult is not None else None})

        #Separates albums between those with Top and those with no Top
        ratedAlbums = [album for album in albums if album['Alex Top']]
        unratedAlbums = [album for album in albums if not album['Alex Top']]
        
        while True:
            sorting_option = input("Choose sorting option (default/compact) [d/c]: ").lower()
            if sorting_option not in ['default','d','compact','c']:
                print("Please enter a valid option")
            else:
                if sorting_option == "c":
                    sorting_option = "compact"
                break

        #Sorts the Rated Albums
        sortedRatedAlbums = sorted(ratedAlbums, key=lambda x: x['Alex Top'])
        last_used_rating = sortedRatedAlbums[0]['Alex Top'] if sortedRatedAlbums else 0

        for i in range(1, len(sortedRatedAlbums)):
            # If the current album's rating is not greater than the last used rating,
            # it means we have a duplicate or a lower value due to previous adjustments.
            # So, we increment the last used rating and assign it to the current book to ensure uniqueness.
            if sortedRatedAlbums[i]['Alex Top'] <= last_used_rating:
                last_used_rating += 1
                sortedRatedAlbums[i]['Alex Top'] = last_used_rating
            else:
                # If no adjustment is needed, just update the last used rating to the current book's rating.
                last_used_rating = sortedRatedAlbums[i]['Alex Top']
                
        # Assign default rating to unrated books
        for album in unratedAlbums:
            album['Alex Top'] = defaultRating

        # Combine and sort the final list
        final_list = sortedRatedAlbums + unratedAlbums

        final_list.sort(key=lambda x: x['Alex Top'])

        highest_rating = final_list[-1]['Alex Top']

        if highest_rating > 99 or len(final_list) > 99:
            # If more than 99, we'll format ratings with leading zeros
            rating_format = '{:03}'  # At least three digits
        else:
            # Otherwise, keep it simple
            rating_format = '{:02}'

        for album in final_list:
            album['Alex Top'] = rating_format.format(album['Alex Top'])

        if sorting_option == "compact":
            # Counter for compacted ratings
            compacted_rating = 1
            for i in range(len(final_list)):
                # Increment compacted rating if the current book's rating is not sequential
                if final_list[i]['Alex Top'] != compacted_rating:
                    final_list[i]['Alex Top'] = rating_format.format(compacted_rating)
                compacted_rating += 1

        print("Uploading to Notion...")
        
        start_time = time.time()
        for index, item in tqdm(enumerate(final_list, start=1), total=len(final_list), desc="Updating Notion"):
            try:
                # Find the corresponding Notion page (modify the filter logic as needed)
                page = next(pg for pg in all_results if pg['properties']['Album']['title'][0]['text']['content'] == item['name'])
                properties = {
                    "Album": {"title": [{"text": {"content": item['name']}}]},
                    "Alex Top": {"select": {"name": item['Alex Top']}}
                }
                notion.pages.update(page['id'], properties=properties)
            except Exception as e:
                print(f"Failed to upload {item}: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"Upload completed in {duration} seconds")

    except Exception as e:
        print(f"An error occurred: {e}")
    decision = input("Is the sorting finished? (y,n)")
    while True:
        if decision in ["y", "n"]:
            if decision == "y":
                break
        else:
            print("Invalid input")
    break