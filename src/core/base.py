import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Album:
    """Shared Album model for managers."""
    name: str
    artist: str
    rating: Optional[int] = None
    status: Optional[str] = None
    page_id: Optional[str] = None
    notion_page: Optional[Dict] = None
    cover_url: Optional[str] = None
    icon_url: Optional[str] = None
    has_cover: bool = False
    has_icon: bool = False

    @property
    def is_listened(self) -> bool:
        return self.status == 'Listened'

    @property
    def is_rated(self) -> bool:
        return self.rating is not None


class BaseNotionManager(ABC):
    """Base class for all Notion managers."""
    
    def __init__(self, api_key: Optional[str] = None, db_id: Optional[str] = None):
        self.api_key = api_key or os.getenv('API_KEY')
        self.db_id = db_id or os.getenv('ALBUM_DB_ID')
        
        if not self.api_key or not self.db_id:
            raise ValueError("API_KEY and ALBUM_DB_ID must be set")
        
        self.notion = Client(auth=self.api_key)
        self.albums: List[Album] = []
    
    @abstractmethod
    def run(self, *args, **kwargs):
        """Main execution method to be implemented by subclasses."""
        pass
    
    def fetch_albums(self) -> List[Album]:
        """Fetch and parse all albums from Notion."""
        from .utils import fetch_all_notion_pages
        
        all_pages = fetch_all_notion_pages(self.notion, self.db_id)
        albums = []
        
        for page in all_pages:
            album = self._parse_notion_page(page)
            if album:
                albums.append(album)
        
        self.albums = albums
        return albums
    
    def _parse_notion_page(self, page: Dict) -> Optional[Album]:
        """Parse a Notion page into an Album object."""
        properties = page['properties']
        
        # Extract album name
        title_data = properties.get('Album', {}).get('title', [])
        name = title_data[0]['text']['content'] if title_data else 'Untitled'
        
        # Extract artist
        artist_data = properties.get('Artist', {}).get('select', {})
        artist = artist_data.get('name', 'Unknown') if artist_data else 'Unknown'
        
        # Extract rating
        rating_data = properties.get('Alex Top', {}).get('select', {})
        rating = None
        if rating_data and rating_data.get('name') and rating_data['name'].isdigit():
            rating = int(rating_data['name'])
        
        # Extract status
        status_data = properties.get('Status', {}).get('status', {})
        status = status_data.get('name', 'Unknown') if status_data else 'Unknown'
        
        return Album(
            name=name,
            artist=artist,
            rating=rating,
            status=status,
            page_id=page['id'],
            notion_page=page,
            has_cover=bool(page.get('cover')),
            has_icon=bool(page.get('icon'))
        )