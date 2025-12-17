import os
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from contextlib import suppress
from dotenv import load_dotenv
from notion_client import Client
from tqdm import tqdm
from utils import (
    clear_console,
    fetch_all_notion_pages
)


@dataclass
class Album:
    """Data class for album information."""
    name: str
    artist: str
    rating: Optional[int]
    status: str
    notion_page: Optional[Dict] = None

    @property
    def is_listened(self) -> bool:
        return self.status == 'Listened'

    @property
    def is_rated(self) -> bool:
        return self.rating is not None


class NotionAlbumManager:
    """Manages album data and operations with Notion."""
    
    def __init__(self, api_key: str, db_id: str):
        self.notion = Client(auth=api_key)
        self.db_id = db_id
        self._albums: List[Album] = []
        self._page_map: Dict[str, Dict] = {}

    def fetch_and_parse_albums(self) -> None:
        """Fetch all albums from Notion and parse them."""
        clear_console()
        print("Retrieving from Notion...")
        start_time = time.time()
        
        all_results = fetch_all_notion_pages(self.notion, self.db_id)
        self._page_map = self._create_page_map(all_results)
        self._albums = self._parse_album_data(all_results)
        
        print(f"Fetched {len(self._albums)} albums in {time.time() - start_time:.2f} seconds.")

    def _create_page_map(self, results: List[Dict]) -> Dict[str, Dict]:
        """Create a map from album name to Notion page for faster lookups."""
        page_map = {}
        for result in results:
            title = result['properties']['Album']['title']
            if title and 'text' in title[0]:
                name = title[0]['text']['content']
                page_map[name] = result
        return page_map

    def _parse_album_data(self, results: List[Dict]) -> List[Album]:
        """Parse raw Notion API results into Album objects."""
        albums = []
        for result in results:
            properties = result['properties']
            
            # Extract album name
            title_data = properties['Album']['title']
            name = title_data[0]['text']['content'] if title_data else 'Untitled'
            
            # Extract rating
            select_data = properties['Alex Top']['select']
            rating = None
            if select_data and select_data['name'] and select_data['name'].isdigit():
                rating = int(select_data['name'])
            
            # Extract artist
            artist_data = properties['Artist']['select']
            artist = artist_data['name'] if artist_data and artist_data['name'] else 'Unknown'
            
            # Extract status
            status_data = properties['Status']['status']
            status = status_data['name'] if status_data and status_data['name'] else 'Unknown'
            
            albums.append(Album(
                name=name,
                artist=artist,
                rating=rating,
                status=status,
                notion_page=result
            ))
        
        return albums

    def _ensure_unique_ratings(self, albums: List[Album]) -> List[Album]:
        """Ensure all albums have unique ratings by incrementing duplicates."""
        if not albums:
            return albums
            
        sorted_albums = sorted(albums, key=lambda x: x.rating or 0)
        last_rating = sorted_albums[0].rating or 0
        
        for i in range(1, len(sorted_albums)):
            current_rating = sorted_albums[i].rating or 0
            if current_rating <= last_rating:
                last_rating += 1
                sorted_albums[i].rating = last_rating
            else:
                last_rating = current_rating
        
        return sorted_albums

    def _assign_default_ratings(self, albums: List[Album], starting_rating: int) -> List[Album]:
        """Assign sequential default ratings to unrated albums."""
        for i, album in enumerate(albums):
            album.rating = starting_rating + i
        return albums

    def _format_ratings(self, albums: List[Album], length: int) -> List[Album]:
        """Format ratings with leading zeros."""
        fmt = '{:0' + str(length) + '}'
        for album in albums:
            album.rating = fmt.format(album.rating)
        return albums

    def _compact_ratings(self, albums: List[Album], length: int) -> List[Album]:
        """Compact ratings to sequential numbers."""
        fmt = '{:0' + str(length) + '}'
        for i, album in enumerate(albums, 1):
            album.rating = fmt.format(i)
        return albums

    def process_albums(self) -> List[Album]:
        """Process albums: separate, fix ratings, and sort."""
        # Filter and categorize
        listened_albums = [a for a in self._albums if a.is_listened]
        rated = [a for a in listened_albums if a.is_rated]
        unrated = [a for a in listened_albums if not a.is_rated]
        
        # Process ratings
        rated = self._ensure_unique_ratings(rated)
        highest_rating = max((a.rating for a in rated), default=0)
        unrated = self._assign_default_ratings(unrated, highest_rating + 1)
        
        # Combine and sort
        final_list = rated + unrated
        final_list.sort(key=lambda x: x.rating)
        
        # Determine formatting length
        if not final_list:
            return final_list
            
        max_rating = final_list[-1].rating
        if isinstance(max_rating, int):
            fmt_length = 3 if max_rating > 99 or len(final_list) > 99 else 2
            final_list = self._format_ratings(final_list, fmt_length)
        
        return final_list

    def update_notion_ratings(self, albums: List[Album]) -> None:
        """Update ratings in Notion database."""
        start_time = time.time()
        
        with tqdm(total=len(albums), desc="Updating Notion") as pbar:
            for album in albums:
                try:
                    page = self._page_map.get(album.name)
                    if not page:
                        print(f"Warning: Could not find page for album '{album.name}'")
                        continue
                    
                    properties = {
                        "Album": {"title": [{"text": {"content": album.name}}]},
                        "Alex Top": {"select": {"name": str(album.rating)}}
                    }
                    self.notion.pages.update(page['id'], properties=properties)
                except Exception as e:
                    print(f"Failed to update '{album.name}': {e}")
                finally:
                    pbar.update(1)
        
        print(f"Upload completed in {time.time() - start_time:.2f} seconds.")


def get_user_choice(prompt: str, valid_options: List[str]) -> str:
    """Get valid user input with retry logic."""
    while True:
        choice = input(prompt).lower().strip()
        if choice in valid_options:
            return choice
        print(f"Please enter one of: {', '.join(valid_options)}")


def main():
    """Main application entry point."""
    load_dotenv()
    
    api_key = os.getenv("API_KEY")
    db_id = os.getenv("ALBUM_DB_ID")
    
    if not api_key or not db_id:
        print("Error: API_KEY and ALBUM_DB_ID must be set in environment variables")
        return
    
    manager = NotionAlbumManager(api_key, db_id)
    
    while True:
        try:
            manager.fetch_and_parse_albums()
            final_list = manager.process_albums()
            
            if not final_list:
                print("No listened albums found to process.")
                continue
            
            # Get user sorting preference
            choice = get_user_choice(
                "Choose sorting option (default/compact) [d/c]: ",
                ['d', 'c', 'default', 'compact']
            )
            
            if choice.startswith('c'):
                fmt_length = 3 if len(final_list) > 99 else 2
                final_list = manager._compact_ratings(final_list, fmt_length)
            
            manager.update_notion_ratings(final_list)
            
        except Exception as e:
            print(f"An error occurred: {e}")
        
        # Ask if finished
        decision = get_user_choice("Is the sorting finished? (y/n): ", ['y', 'n'])
        if decision == "y":
            break


if __name__ == "__main__":
    main()