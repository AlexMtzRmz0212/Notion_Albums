import requests
import time
import os
from typing import Optional, Dict
from ..core.base import BaseNotionManager, Album


class AlbumDecorator(BaseNotionManager):
    """Manages album cover and icon decorations from Spotify."""
    
    def __init__(self, api_key: str = None, db_id: str = None):
        super().__init__(api_key, db_id)
        self.spotify_token: Optional[str] = None
        self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    def run(self, update_existing: bool = False) -> None:
        """Main execution method."""
        print("🎨 Starting album decoration...")
        
        # Fetch albums
        albums = self.fetch_albums()
        print(f"Found {len(albums)} total albums")
        
        # Filter albums needing decoration
        to_process = [
            album for album in albums 
            if update_existing or (not album.has_cover or not album.has_icon)
        ]
        
        if not to_process:
            print("All albums already decorated! Use update_existing=True to force update")
            return
        
        print(f"Processing {len(to_process)} albums...")
        
        successful = 0
        for album in to_process:
            if self.decorate_album(album, update_existing):
                successful += 1
            time.sleep(0.5)  # Rate limiting
        
        print(f"✓ Successfully decorated {successful}/{len(to_process)} albums")
    
    def decorate_album(self, album: Album, update_existing: bool) -> bool:
        """Decorate a single album with cover and icon."""
        print(f"\nProcessing: '{album.name}' by {album.artist}")
        
        # Search Spotify
        spotify_data = self.search_spotify_album(album.name, album.artist)
        if not spotify_data:
            return False
        
        # Determine what to update
        cover_url = spotify_data['cover_url'] if not album.has_cover or update_existing else None
        icon_url = spotify_data['icon_url'] if not album.has_icon or update_existing else None
        
        # Update Notion
        return self.update_page_decorations(album.page_id, cover_url, icon_url)
    
    def get_spotify_token(self) -> str:
        """Get Spotify API access token."""
        auth_response = requests.post(
            'https://accounts.spotify.com/api/token',
            data={
                'grant_type': 'client_credentials',
                'client_id': self.spotify_client_id,
                'client_secret': self.spotify_client_secret,
            }
        )
        
        if auth_response.status_code == 200:
            self.spotify_token = auth_response.json()['access_token']
            return self.spotify_token
        else:
            raise Exception(f"Spotify auth failed: {auth_response.text}")
    
    def search_spotify_album(self, album_name: str, artist_name: str) -> Optional[Dict]:
        """Search Spotify for album artwork."""
        if not self.spotify_token:
            self.get_spotify_token()
        
        query = f"album:{album_name} artist:{artist_name}"
        encoded_query = requests.utils.quote(query)
        url = f'https://api.spotify.com/v1/search?q={encoded_query}&type=album&limit=1'
        
        headers = {'Authorization': f'Bearer {self.spotify_token}'}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                if data['albums']['items']:
                    album = data['albums']['items'][0]
                    cover_url = album['images'][0]['url'] if album['images'] else None
                    icon_url = album['images'][-1]['url'] if album['images'] else None
                    
                    return {
                        'cover_url': cover_url,
                        'icon_url': icon_url,
                        'album_name': album['name'],
                        'artist_name': album['artists'][0]['name'] if album['artists'] else None
                    }
            
            print(f"  No album found for '{album_name}' by '{artist_name}'")
            return None
            
        except Exception as e:
            print(f"  Error searching Spotify: {e}")
            return None
    
    def update_page_decorations(self, page_id: str, cover_url: str = None, icon_url: str = None) -> bool:
        """Update Notion page with cover and icon."""
        payload = {}
        
        if cover_url:
            payload['cover'] = {
                'type': 'external',
                'external': {'url': cover_url}
            }
        
        if icon_url:
            payload['icon'] = {
                'type': 'external',
                'external': {'url': icon_url}
            }
        
        if not payload:
            return False
        
        try:
            self.notion.pages.update(page_id, **payload)
            
            updates = []
            if cover_url: updates.append("cover")
            if icon_url: updates.append("icon")
            print(f"  ✓ Updated {', '.join(updates)}")
            return True
            
        except Exception as e:
            print(f"  ✗ Failed to update page: {e}")
            return False