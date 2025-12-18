from typing import List
from tqdm import tqdm

try:
    from core.base import BaseNotionManager, Album
except ImportError:
    try:
        from src.core.base import BaseNotionManager, Album
    except ImportError:
        # Last resort: relative import
        from ..core.base import BaseNotionManager, Album


class AlbumSorter(BaseNotionManager):
    """Manages album sorting and rating operations."""
    
    def __init__(self, api_key: str = None, db_id: str = None):
        super().__init__(api_key, db_id)
    
    def run(self, compact_mode: bool = False) -> None:
        """Main execution method."""
        print("🎵 Starting album sorting...")
        
        # Fetch albums
        albums = self.fetch_albums()
        print(f"Found {len(albums)} total albums")
        
        # Process and update
        processed = self.process_albums()
        if compact_mode:
            processed = self._compact_ratings(processed)
        
        self.update_notion_ratings(processed)
    
    def process_albums(self) -> List[Album]:
        """Process albums: separate, fix ratings, and sort."""
        # Filter listened albums only
        listened = [a for a in self.albums if a.is_listened]
        
        # Separate rated and unrated
        rated = [a for a in listened if a.is_rated]
        unrated = [a for a in listened if not a.is_rated]
        
        # Process ratings
        rated = self._ensure_unique_ratings(rated)
        highest = max((a.rating for a in rated), default=0)
        unrated = self._assign_default_ratings(unrated, highest + 1)
        
        # Combine and sort
        final = rated + unrated
        final.sort(key=lambda x: x.rating)
        
        # Format ratings
        if final:
            fmt_length = 3 if final[-1].rating > 99 or len(final) > 99 else 2
            final = self._format_ratings(final, fmt_length)
        
        return final
    
    def _ensure_unique_ratings(self, albums: List[Album]) -> List[Album]:
        """Ensure all albums have unique ratings."""
        if not albums:
            return albums
        
        sorted_albums = sorted(albums, key=lambda x: x.rating)
        last_rating = sorted_albums[0].rating
        
        for i in range(1, len(sorted_albums)):
            if sorted_albums[i].rating <= last_rating:
                last_rating += 1
                sorted_albums[i].rating = last_rating
            else:
                last_rating = sorted_albums[i].rating
        
        return sorted_albums
    
    def _assign_default_ratings(self, albums: List[Album], start: int) -> List[Album]:
        """Assign sequential ratings to unrated albums."""
        for i, album in enumerate(albums):
            album.rating = start + i
        return albums
    
    def _format_ratings(self, albums: List[Album], length: int) -> List[Album]:
        """Format ratings with leading zeros."""
        fmt = f'{{:0{length}d}}'
        for album in albums:
            album.rating = fmt.format(album.rating)
        return albums
    
    def _compact_ratings(self, albums: List[Album]) -> List[Album]:
        """Compact ratings to sequential numbers."""
        if not albums:
            return albums
        
        fmt_length = 3 if len(albums) > 99 else 2
        for i, album in enumerate(albums, 1):
            album.rating = f'{i:0{fmt_length}d}'
        return albums
    
    def update_notion_ratings(self, albums: List[Album]) -> None:
        """Update ratings in Notion."""
        print(f"Updating {len(albums)} albums in Notion...")
        
        with tqdm(total=len(albums), desc="Updating Notion") as pbar:
            for album in albums:
                try:
                    properties = {
                        "Alex Top": {"select": {"name": str(album.rating)}}
                    }
                    self.notion.pages.update(album.page_id, properties=properties)
                except Exception as e:
                    print(f"Failed to update '{album.name}': {e}")
                finally:
                    pbar.update(1)
        
        print("✓ Ratings updated successfully!")