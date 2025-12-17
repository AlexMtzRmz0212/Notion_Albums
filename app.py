# app.py
import streamlit as st
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add project root to path for module imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

load_dotenv()

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

def log_message(message, level="INFO"):
    """Add message to log with timestamp"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}"
    st.session_state.logs.append(log_entry)
    
    # Keep only last 100 logs
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

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

def simulate_operation(operation_name, duration=2):
    """Simulate an operation (to be replaced with actual functions)"""
    import time
    st.session_state.is_running = True
    st.session_state.operation_status[operation_name] = "running"
    
    log_message(f"Starting {operation_name.replace('_', ' ')}...")
    
    try:
        # Simulate work
        time.sleep(duration)
        
        # Simulate success
        st.session_state.operation_status[operation_name] = "success"
        st.session_state.last_operation = operation_name
        log_message(f"Completed {operation_name.replace('_', ' ')} successfully!")
        
    except Exception as e:
        st.session_state.operation_status[operation_name] = "error"
        log_message(f"Error during {operation_name.replace('_', ' ')}: {str(e)}", level="ERROR")
    
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
    # Placeholder for actual database stats
    st.write("Albums: --")
    st.write("Songs: --")
    st.write("Artists: --")
    
    st.markdown("---")
    
    # Actions
    st.markdown("### Actions")
    if st.button("🔄 Reset Status", use_container_width=True):
        reset_operation_status()
        log_message("Status reset")
    
    if st.button("🗑️ Clear Logs", use_container_width=True):
        st.session_state.logs = []
        log_message("Logs cleared")

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
    
    with col2:
        st.markdown("###")
        if st.button(
            "Run",
            key="set_covers_btn",
            disabled=st.session_state.is_running,
            type="primary"
        ):
            simulate_operation("set_covers")
    
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
    
    with col2:
        starting_rank = st.number_input(
            "Starting rank for unrated:",
            min_value=1,
            value=1,
            key="starting_rank"
        )
    
    with col3:
        st.markdown("###")
        if st.button(
            "Run",
            key="sort_albums_btn",
            disabled=st.session_state.is_running,
            type="primary"
        ):
            simulate_operation("sort_albums")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Card 3: Create Song Pages
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎶 Create Song Pages")
    st.markdown("Expand albums into individual song pages.")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        batch_size = st.slider(
            "Albums per batch:",
            min_value=1,
            max_value=50,
            value=10,
            key="batch_size"
        )
    
    with col2:
        include_all = st.checkbox(
            "Include albums without songs",
            value=False,
            key="include_all"
        )
    
    with col3:
        st.markdown("###")
        if st.button(
            "Run",
            key="create_songs_btn",
            disabled=st.session_state.is_running,
            type="primary"
        ):
            simulate_operation("create_songs")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Progress and Status Section
st.markdown('<h2 class="sub-header">Operation Status</h2>', unsafe_allow_html=True)

if st.session_state.is_running:
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate progress (to be replaced with actual progress tracking)
    for i in range(100):
        progress_bar.progress(i + 1)
        status_text.text(f"Processing... {i + 1}%")
        import time
        time.sleep(0.02)
    
    progress_bar.empty()
    status_text.empty()

# Log Output
st.markdown('<h2 class="sub-header">Activity Log</h2>', unsafe_allow_html=True)

log_container = st.container()
with log_container:
    # Display logs in reverse order (newest first)
    for log_entry in reversed(st.session_state.logs[-20:]):  # Show last 20 logs
        st.text(log_entry)

# Bottom Status Bar
st.markdown("---")
col1, col2 = st.columns([1, 3])
with col1:
    if st.session_state.is_running:
        st.warning("⏳ Operation in progress...")
    else:
        st.success("✅ Ready for operations")

with col2:
    st.caption(f"Total logs: {len(st.session_state.logs)} | Last update: {st.session_state.last_operation or 'None'}")

# Information Panel (expandable)
with st.expander("ℹ️ About this application"):
    st.markdown("""
    ### Notion Music Manager
    
    **Purpose:** Automate music library management in Notion
    
    **Features:**
    1. **Album Covers:** Fetch album artwork from Spotify
    2. **Album Sorting:** Rank and organize albums by rating
    3. **Song Pages:** Create individual pages for songs
    
    **Configuration:** Ensure your `.env` file contains:
    ```
    API_KEY=your_notion_api_key
    ALBUM_DB_ID=your_database_id
    SPOTIFY_CLIENT_ID=your_spotify_client_id
    SPOTIFY_CLIENT_SECRET=your_spotify_secret
    ```
    
    **Next Steps:**
    - Connect the actual functions from `cover.py` and `Album Sorter.py`
    - Add error handling and recovery
    - Implement batch processing for large libraries
    """)