import os
import requests
import time
from dotenv import load_dotenv
from utils import fetch_all_notion_pages, clear_console
from notion_client import Client

load_dotenv()

class NotionPageDecorator:
    def __init__(self):
        self.notion_token = os.getenv('API_KEY')
        self.database_id = os.getenv('ALBUM_DB_ID')
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        self.notion_headers = {
            'Authorization': f'Bearer {self.notion_token}',
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        self.spotify_token = None

    def get_spotify_token(self):
        """Get Spotify API access token"""
        auth_url = 'https://accounts.spotify.com/api/token'
        auth_response = requests.post(auth_url, {
            'grant_type': 'client_credentials',
            'client_id': self.spotify_client_id,
            'client_secret': self.spotify_client_secret,
        })
        
        if auth_response.status_code == 200:
            self.spotify_token = auth_response.json()['access_token']
            print("✓ Successfully authenticated with Spotify API")
        else:
            raise Exception(f"Spotify authentication failed: {auth_response.text}")

    def search_spotify_album(self, album_name, artist_name):
        """Search Spotify for album data including cover URL"""
        if not self.spotify_token:
            self.get_spotify_token()
            
        query = f"album:{album_name} artist:{artist_name}"
        encoded_query = requests.utils.quote(query)
        url = f'https://api.spotify.com/v1/search?q={encoded_query}&type=album&limit=1'
        
        headers = {
            'Authorization': f'Bearer {self.spotify_token}'
        }
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                if data['albums']['items'] and len(data['albums']['items']) > 0:
                    album_data = data['albums']['items'][0]
                    
                    # Get largest cover for page cover, smaller one for icon
                    cover_url = album_data['images'][0]['url'] if album_data['images'] else None
                    icon_url = album_data['images'][-1]['url'] if album_data['images'] else None  # Smallest image
                    
                    return {
                        'cover_url': cover_url,
                        'icon_url': icon_url,
                        'album_name': album_data['name'],
                        'artist_name': album_data['artists'][0]['name'] if album_data['artists'] else None
                    }
            
            print(f"  No album found for '{album_name}' by '{artist_name}'")
            return None
            
        except Exception as e:
            print(f"  Error searching Spotify for '{album_name}': {e}")
            return None

    def get_albums_to_decorate(self):
        """Fetch albums from Notion that might need covers/icons"""
        # url = f'https://api.notion.com/v1/databases/{self.database_id}/query'
        
        # response = requests.post(url, headers=self.notion_headers)
        
        # if response.status_code != 200:
        #     raise Exception(f"Failed to fetch Notion database: {response.text}")
        # data = response.json()
        
        all_pages = fetch_all_notion_pages(Client(auth=self.notion_token), self.database_id)
        albums = []
        # pprint.pprint(all_pages)
        # pprint.pprint(all_pages[0])
        # pprint.pprint(all_pages[-1])

        for page in all_pages:
            properties = page['properties']
            
            # Get album name (title property)
            album_name = None
            if 'Album' in properties and properties['Album']['title']:
                album_name = properties['Album']['title'][0]['plain_text']
            
            # Get artist name (select property)
            artist_name = None
            if 'Artist' in properties and properties['Artist']['select']:
                artist_name = properties['Artist']['select']['name']
            
            if album_name and artist_name:
                albums.append({
                    'page_id': page['id'],
                    'album_name': album_name,
                    'artist_name': artist_name,
                    'has_cover': bool(page.get('cover')),
                    'has_icon': bool(page.get('icon'))
                })
        
        return albums

    def update_page_decorations(self, page_id, cover_url=None, icon_url=None):
        """Update a Notion page with cover and/or icon"""
        url = f'https://api.notion.com/v1/pages/{page_id}'
        
        payload = {}
        
        # Add cover if provided
        if cover_url:
            payload['cover'] = {
                'type': 'external',
                'external': {
                    'url': cover_url
                }
            }
        
        # Add icon if provided  
        if icon_url:
            payload['icon'] = {
                'type': 'external',
                'external': {
                    'url': icon_url
                }
            }
        
        if not payload:
            return False  # Nothing to update
        
        response = requests.patch(url, json=payload, headers=self.notion_headers)
        
        if response.status_code == 200:
            updates = []
            if cover_url: updates.append("cover")
            if icon_url: updates.append("icon")
            print(f"  ✓ Updated {', '.join(updates)}")
            return True
        else:
            print(f"  ✗ Failed to update page: {response.text}")
            return False

    def run(self, update_existing=False):
        """Main function to decorate album pages"""
        print("🎵 Starting album page decoration...")
        
        # Get all albums
        albums = self.get_albums_to_decorate()
        print(f"Found {len(albums)} albums in database")
        # pprint.pprint(albums)
        
        if not albums:
            print("No albums found!")
            return
        
        albums_to_process = []
        for album in albums:
            if update_existing or (not album['has_cover'] and not album['has_icon']):
                albums_to_process.append(album)
        
        print(f"Processing {len(albums_to_process)} albums that need decoration")
        
        if not albums_to_process:
            print("All albums already have covers/icons! Use update_existing=True to force update")
            return
        
        successful_updates = 0
        
        for album in albums_to_process:
            print(f"\nProcessing: '{album['album_name']}' by {album['artist_name']}")
            print(f"  Current: cover={'✓' if album['has_cover'] else '✗'} icon={'✓' if album['has_icon'] else '✗'}")
            
            # Search for album data
            album_data = self.search_spotify_album(album['album_name'], album['artist_name'])
            
            if album_data:
                # Determine what to update
                cover_url = album_data['cover_url'] if not album['has_cover'] or update_existing else None
                icon_url = album_data['icon_url'] if not album['has_icon'] or update_existing else None
                
                # Update page
                if self.update_page_decorations(album['page_id'], cover_url, icon_url):
                    successful_updates += 1
                
                # Be nice to the APIs
                time.sleep(0.5)
        
        print(f"\n🎉 Complete! Successfully updated {successful_updates} out of {len(albums_to_process)} albums")

def main():

    clear_console()
    decorator = NotionPageDecorator()
    
    # Choose one of these options:
    
    # Option 1: Only add missing covers/icons (recommended for first run)
    decorator.run(update_existing=False)
    
    # Option 2: Update ALL albums (will overwrite existing covers/icons)
    # decorator.run(update_existing=True)

if __name__ == '__main__':
    main()