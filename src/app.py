# app.py
import streamlit as st
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
import time

# Get the current file's directory (src folder)
current_dir = Path(__file__).parent
# Get the project root (parent of src)
project_root = current_dir.parent

# Add both to Python path - IMPORTANT: Add src first!
sys.path.insert(0, str(current_dir))  # Add src directory
sys.path.insert(0, str(project_root))  # Add project root

# Now try the imports
try:
    from managers.sorter import AlbumSorter
    from managers.decorator import AlbumDecorator
except ImportError as e:
    print(f"Import error: {e}")
    # Try alternative import path
    try:
        from src.managers.sorter import AlbumSorter
        from src.managers.decorator import AlbumDecorator
    except ImportError:
        raise

# Page configuration
st.set_page_config(
    page_title="🎵 Notion Music Manager",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1DB954;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #FFFFFF;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1DB954;
    }
    .success-box {
        background-color: #0A2F1C;
        border: 1px solid #1DB954;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #1A1A2E;
        border: 1px solid #3498DB;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background-color: #1DB954;
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1ED760;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .danger-button>button {
        background-color: #E74C3C;
    }
    .danger-button>button:hover {
        background-color: #C0392B;
    }
    .secondary-button>button {
        background-color: #7F8C8D;
    }
    .secondary-button>button:hover {
        background-color: #95A5A6;
    }
    .log-info {
        color: #3498DB;
    }
    .log-success {
        color: #2ECC71;
    }
    .log-warning {
        color: #F39C12;
    }
    .log-error {
        color: #E74C3C;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'last_operation' not in st.session_state:
    st.session_state.last_operation = None
if 'operation_status' not in st.session_state:
    st.session_state.operation_status = {}
if 'is_running' not in st.session_state:
    st.session_state.is_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'album_stats' not in st.session_state:
    st.session_state.album_stats = {}
if 'managers' not in st.session_state:
    st.session_state.managers = {
        'sorter': None,
        'decorator': None
    }

def log_message(message: str, level: str = "INFO"):
    """Add message to log with timestamp"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    st.session_state.logs.append(log_entry)
    
    # Keep only last 100 logs
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

def get_manager(manager_type: str):
    """Get or create a manager instance"""
    if manager_type not in st.session_state.managers:
        return None
        
    if st.session_state.managers[manager_type] is None:
        try:
            if manager_type == 'sorter':
                st.session_state.managers[manager_type] = AlbumSorter()
                log_message(f"Created {manager_type} manager", "INFO")
            elif manager_type == 'decorator':
                st.session_state.managers[manager_type] = AlbumDecorator()
                log_message(f"Created {manager_type} manager", "INFO")
        except Exception as e:
            log_message(f"Failed to create {manager_type} manager: {str(e)}", "ERROR")
            return None
    
    return st.session_state.managers[manager_type]

def show_status_indicator(status):
    """Show a status indicator"""
    if status == "success":
        return "✅"
    elif status == "error":
        return "❌"
    elif status == "running":
        return "⏳"
    else:
        return "⚪"

def reset_operation_status():
    """Reset all operation statuses"""
    st.session_state.operation_status = {
        "set_covers": None,
        "sort_albums": None,
        "create_songs": None
    }
    st.session_state.is_running = False
    log_message("Status reset", "INFO")

def update_album_stats():
    """Fetch and update album statistics"""
    try:
        sorter = get_manager('sorter')
        if sorter:
            albums = sorter.fetch_albums()
            
            # Count listened albums
            listened_albums = [a for a in albums if a.is_listened]
            rated_albums = [a for a in listened_albums if a.is_rated]
            
            # Count albums with covers/icons
            albums_with_covers = [a for a in albums if a.has_cover]
            albums_with_icons = [a for a in albums if a.has_icon]
            
            st.session_state.album_stats = {
                'total_albums': len(albums),
                'listened_albums': len(listened_albums),
                'rated_albums': len(rated_albums),
                'albums_with_covers': len(albums_with_covers),
                'albums_with_icons': len(albums_with_icons),
                'unrated_albums': len(listened_albums) - len(rated_albums),
                'albums_without_covers': len(albums) - len(albums_with_covers),
                'albums_without_icons': len(albums) - len(albums_with_icons)
            }
            log_message("Album statistics updated", "INFO")
    except Exception as e:
        log_message(f"Failed to update album stats: {str(e)}", "ERROR")

def run_set_covers(update_existing: bool = False):
    """Run the album cover decorator"""
    st.session_state.is_running = True
    st.session_state.operation_status["set_covers"] = "running"
    
    log_message(f"Starting album decoration (update_existing={update_existing})...", "INFO")
    
    try:
        decorator = get_manager('decorator')
        if not decorator:
            raise Exception("Failed to initialize decorator")
        
        # Create a placeholder for progress
        progress_placeholder = st.empty()
        status_placeholder = st.empty()
        
        # Run decorator
        decorator.run(update_existing=update_existing)
        
        # Update status
        st.session_state.operation_status["set_covers"] = "success"
        st.session_state.last_operation = "set_covers"
        log_message("Album decoration completed successfully!", "SUCCESS")
        
        # Update stats
        update_album_stats()
        
    except Exception as e:
        st.session_state.operation_status["set_covers"] = "error"
        log_message(f"Error during album decoration: {str(e)}", "ERROR")
    
    st.session_state.is_running = False

def run_sort_albums(compact_mode: bool = False, starting_rank: int = 1):
    """Run the album sorter"""
    st.session_state.is_running = True
    st.session_state.operation_status["sort_albums"] = "running"
    
    log_message(f"Starting album sorting (compact_mode={compact_mode}, starting_rank={starting_rank})...", "INFO")
    
    try:
        sorter = get_manager('sorter')
        if not sorter:
            raise Exception("Failed to initialize sorter")
        
        # Fetch albums first
        albums = sorter.fetch_albums()
        log_message(f"Fetched {len(albums)} albums", "INFO")
        
        # Process albums
        processed = sorter.process_albums()
        
        # Apply compact mode if requested
        if compact_mode:
            processed = sorter._compact_ratings(processed)
        
        # Update Notion
        if processed:
            sorter.update_notion_ratings(processed)
        
        # Update status
        st.session_state.operation_status["sort_albums"] = "success"
        st.session_state.last_operation = "sort_albums"
        log_message(f"Album sorting completed! Processed {len(processed)} albums", "SUCCESS")
        
        # Update stats
        update_album_stats()
        
    except Exception as e:
        st.session_state.operation_status["sort_albums"] = "error"
        log_message(f"Error during album sorting: {str(e)}", "ERROR")
    
    st.session_state.is_running = False

# Sidebar
with st.sidebar:
    st.markdown("## 🎵 Settings")
    
    # API Status
    st.markdown("### API Status")
    api_key_status = "✅ Configured" if os.getenv("API_KEY") else "❌ Missing"
    notion_db_status = "✅ Configured" if os.getenv("ALBUM_DB_ID") else "❌ Missing"
    spotify_status = "✅ Configured" if os.getenv("SPOTIFY_CLIENT_ID") and os.getenv("SPOTIFY_CLIENT_SECRET") else "❌ Missing"
    
    st.write(f"**Notion API:** {api_key_status}")
    st.write(f"**Album Database:** {notion_db_status}")
    st.write(f"**Spotify API:** {spotify_status}")
    
    st.markdown("---")
    
    # Operations History
    st.markdown("### Recent Operations")
    if st.session_state.last_operation:
        st.success(f"Last: {st.session_state.last_operation.replace('_', ' ').title()}")
    
    st.markdown("---")
    
    # Database Info
    st.markdown("### Database Info")
    
    # Update stats button
    if st.button("📊 Update Stats", use_container_width=True):
        update_album_stats()
    
    # Display stats if available
    if st.session_state.album_stats:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Albums", st.session_state.album_stats['total_albums'])
            st.metric("Listened", st.session_state.album_stats['listened_albums'])
            st.metric("With Covers", st.session_state.album_stats['albums_with_covers'])
        with col2:
            st.metric("Rated", st.session_state.album_stats['rated_albums'])
            st.metric("With Icons", st.session_state.album_stats['albums_with_icons'])
            st.metric("Unrated", st.session_state.album_stats['unrated_albums'])
    else:
        st.info("Click 'Update Stats' to load database information")
    
    st.markdown("---")
    
    # Actions
    st.markdown("### Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset Status", use_container_width=True):
            reset_operation_status()
    
    with col2:
        if st.button("🗑️ Clear Logs", use_container_width=True):
            st.session_state.logs = []
            log_message("Logs cleared", "INFO")
    
    st.markdown("---")
    
    # Initialize Managers
    st.markdown("### System")
    if st.button("🚀 Initialize Managers", use_container_width=True):
        with st.spinner("Initializing..."):
            # Initialize both managers
            sorter = get_manager('sorter')
            decorator = get_manager('decorator')
            
            if sorter and decorator:
                st.success("Managers initialized!")
                update_album_stats()
            else:
                st.error("Failed to initialize managers")

# Main content
st.markdown('<h1 class="main-header">🎵 Notion Music Manager</h1>', unsafe_allow_html=True)

# Status Overview
col1, col2, col3 = st.columns(3)
with col1:
    status = st.session_state.operation_status.get("set_covers", None)
    st.metric(
        "Album Covers",
        show_status_indicator(status),
        delta=None
    )
with col2:
    status = st.session_state.operation_status.get("sort_albums", None)
    st.metric(
        "Album Sorting",
        show_status_indicator(status),
        delta=None
    )
with col3:
    status = st.session_state.operation_status.get("create_songs", None)
    st.metric(
        "Song Pages",
        show_status_indicator(status),
        delta=None
    )

# Operation Cards
st.markdown('<h2 class="sub-header">Operations</h2>', unsafe_allow_html=True)

# Card 1: Set Album Covers
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🖼️ Set Album Covers")
    st.markdown("Fetch album covers and icons from Spotify and update Notion pages.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        cover_option = st.radio(
            "Update mode:",
            ["Add missing only", "Update all (overwrite existing)"],
            key="cover_option"
        )
        update_existing = cover_option == "Update all (overwrite existing)"
        
        # Show stats if available
        if st.session_state.album_stats:
            st.info(f"""
            **Current Status:**
            - {st.session_state.album_stats['albums_with_covers']}/{st.session_state.album_stats['total_albums']} albums have covers
            - {st.session_state.album_stats['albums_with_icons']}/{st.session_state.album_stats['total_albums']} albums have icons
            """)
    
    with col2:
        st.markdown("###")
        if st.button(
            "🎨 Run Decorator",
            key="set_covers_btn",
            disabled=st.session_state.is_running,
            type="primary",
            use_container_width=True
        ):
            run_set_covers(update_existing)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Card 2: Sort Albums
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📊 Sort Albums")
    st.markdown("Sort albums by rating and update rankings in Notion.")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sort_option = st.selectbox(
            "Sorting method:",
            ["Default ranking", "Compact ranking"],
            key="sort_option"
        )
        compact_mode = sort_option == "Compact ranking"
    
    with col2:
        starting_rank = st.number_input(
            "Starting rank for unrated:",
            min_value=1,
            value=1,
            key="starting_rank"
        )
        
        # Show stats if available
        if st.session_state.album_stats:
            st.caption(f"Found {st.session_state.album_stats['unrated_albums']} unrated albums")
    
    with col3:
        st.markdown("###")
        if st.button(
            "📈 Run Sorter",
            key="sort_albums_btn",
            disabled=st.session_state.is_running,
            type="primary",
            use_container_width=True
        ):
            run_sort_albums(compact_mode, starting_rank)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Card 3: Create Song Pages (Placeholder for future feature)
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎶 Create Song Pages")
    st.markdown("Expand albums into individual song pages. (Coming Soon)")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        batch_size = st.slider(
            "Albums per batch:",
            min_value=1,
            max_value=50,
            value=10,
            key="batch_size",
            disabled=True
        )
    
    with col2:
        include_all = st.checkbox(
            "Include albums without songs",
            value=False,
            key="include_all",
            disabled=True
        )
    
    with col3:
        st.markdown("###")
        if st.button(
            "Run",
            key="create_songs_btn",
            disabled=True,
            type="secondary",
            use_container_width=True
        ):
            pass
    
    st.markdown("</div>", unsafe_allow_html=True)

# Progress and Status Section
st.markdown('<h2 class="sub-header">Operation Status</h2>', unsafe_allow_html=True)

if st.session_state.is_running:
    # Show progress bar for running operations
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simple progress simulation
    for i in range(100):
        progress_bar.progress(i + 1)
        status_text.text(f"Processing... {i + 1}%")
        time.sleep(0.01)
    
    progress_bar.empty()
    status_text.empty()

# Log Output
st.markdown('<h2 class="sub-header">Activity Log</h2>', unsafe_allow_html=True)

log_container = st.container()
with log_container:
    # Create tabs for different log levels
    log_tabs = st.tabs(["All", "INFO", "SUCCESS", "WARNING", "ERROR"])
    
    with log_tabs[0]:  # All logs
        # Display logs in reverse order (newest first)
        for log_entry in reversed(st.session_state.logs[-20:]):  # Show last 20 logs
            color_class = f"log-{log_entry['level'].lower()}"
            st.markdown(
                f"<span class='{color_class}'>[{log_entry['timestamp']}] "
                f"[{log_entry['level']}] {log_entry['message']}</span>",
                unsafe_allow_html=True
            )
    
    # Filtered logs for other tabs
    for i, level in enumerate(["INFO", "SUCCESS", "WARNING", "ERROR"], 1):
        with log_tabs[i]:
            filtered_logs = [log for log in st.session_state.logs if log['level'] == level]
            for log_entry in reversed(filtered_logs[-10:]):
                color_class = f"log-{log_entry['level'].lower()}"
                st.markdown(
                    f"<span class='{color_class}'>[{log_entry['timestamp']}] "
                    f"{log_entry['message']}</span>",
                    unsafe_allow_html=True
                )
            if not filtered_logs:
                st.info(f"No {level} logs")

# Bottom Status Bar
st.markdown("---")
col1, col2 = st.columns([1, 3])
with col1:
    if st.session_state.is_running:
        st.warning("⏳ Operation in progress...")
    else:
        managers_ready = all(st.session_state.managers.values())
        if managers_ready:
            st.success("✅ Ready for operations")
        else:
            st.warning("⚠️ Initialize managers first")

with col2:
    last_op = st.session_state.last_operation or 'None'
    st.caption(f"Total logs: {len(st.session_state.logs)} | Last operation: {last_op}")

# Information Panel (expandable)
with st.expander("ℹ️ About this application"):
    st.markdown("""
    ### Notion Music Manager
    
    **Purpose:** Automate music library management in Notion using the refactored code structure.
    
    **Features:**
    1. **Album Covers:** Fetch album artwork from Spotify using `AlbumDecorator`
    2. **Album Sorting:** Rank and organize albums by rating using `AlbumSorter`
    3. **Unified Architecture:** Shared `Album` model and `BaseNotionManager` base class
    
    **How to use:**
    1. Click "Initialize Managers" in the sidebar
    2. Update stats to see current database status
    3. Choose an operation and click "Run"
    
    **Configuration:** Ensure your `.env` file contains:
    ```env
    API_KEY=your_notion_api_key
    ALBUM_DB_ID=your_database_id
    SPOTIFY_CLIENT_ID=your_spotify_client_id
    SPOTIFY_CLIENT_SECRET=your_spotify_secret
    ```
    
    **Project Structure:**
    ```
    src/
    ├── core/
    │   ├── base.py           # BaseNotionManager and Album model
    │   └── utils.py          # Shared utilities
    ├── managers/
    │   ├── sorter.py         # AlbumSorter
    │   └── decorator.py      # AlbumDecorator
    └── app.py               # This Streamlit app
    ```
    """)

# Initialize on first run
if st.session_state.managers['sorter'] is None or st.session_state.managers['decorator'] is None:
    st.info("👈 Please initialize managers from the sidebar to get started!")