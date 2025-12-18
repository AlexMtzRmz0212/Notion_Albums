import os

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def fetch_all_notion_pages(notion_client, db_id):
    all_pages = []
    response = notion_client.databases.query(database_id=db_id)
    
    all_pages.extend(response['results'])

    while response.get('has_more', False):
        response = notion_client.databases.query(
            database_id=db_id,
            start_cursor=response['next_cursor']
        )
        all_pages.extend(response['results'])

    return all_pages