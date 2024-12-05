import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Page Configuration
st.set_page_config(
    layout="wide",
    page_title="YouTube Viral ChatBot",
    page_icon="🚀",
)

# Initialize session state for API key
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""

def get_service():
    """Initialize YouTube Data API client."""
    api_key = st.session_state.get("api_key")
    if not api_key:
        st.error("YouTube API key is missing. Please enter it in the sidebar to continue.")
        st.stop()
    try:
        return build("youtube", "v3", developerKey=api_key)
    except Exception as e:
        st.error(f"Invalid API key or failed to initialize YouTube API client: {e}")
        st.stop()

# Helper Function: Extract Channel ID
def extract_channel_id(channel_url):
    """Extract the channel ID from a YouTube channel URL."""
    if "youtube.com/channel/" in channel_url:
        return channel_url.split("channel/")[-1]
    elif "youtube.com/c/" in channel_url or "youtube.com/user/" in channel_url:
        st.error("Custom channel URLs are not supported. Please provide a direct channel ID URL.")
        st.stop()
    else:
        st.error("Invalid channel URL. Please provide a valid YouTube channel URL.")
        st.stop()

# Test API Key
def test_api_key():
    """Test the validity of the YouTube API key."""
    try:
        youtube = get_service()
        youtube.channels().list(part="snippet", forUsername="Google").execute()
        st.sidebar.success("API key is valid!")
    except Exception as e:
        st.sidebar.error(f"API key validation failed: {e}")
        st.stop()

# Sidebar: API Key Input
st.sidebar.write("## API Configuration")
st.sidebar.text_input(
    "Enter YouTube API Key:",
    type="password",
    key="api_key",
    help="Enter your YouTube API key to enable functionality.",
)

# Test API Key Before Proceeding
if st.sidebar.button("Test API Key"):
    test_api_key()

# Ensure API key is entered
if not st.session_state["api_key"]:
    st.sidebar.warning("Please enter your YouTube API key to continue.")
    st.stop()

# Earnings Estimation Helper Functions
def estimate_video_earnings(video_url):
    """Estimate earnings for a single video."""
    youtube = get_service()
    video_id = video_url.split("v=")[-1]
    try:
        response = youtube.videos().list(part="statistics", id=video_id).execute()

        if 'items' in response and response['items']:
            stats = response['items'][0]['statistics']
            view_count = int(stats.get('viewCount', 0))
            cpi_min, cpi_max = 0.2, 4.0  # CPM range
            min_earnings = (view_count * cpi_min) / 1000
            max_earnings = (view_count * cpi_max) / 1000

            st.write(f"### Estimated Earnings for Video")
            st.write(f"Estimated Earnings Range: ${min_earnings:.2f} - ${max_earnings:.2f}")

            # Plot Earnings
            fig, ax = plt.subplots()
            ax.bar(["Min Earnings", "Max Earnings"], [min_earnings, max_earnings], color=["#ff4500", "#ffa07a"])
            plt.title("Video Earnings Range")
            st.pyplot(fig)
        else:
            st.error("No data found for the specified video.")
    except HttpError as e:
        st.error(f"An error occurred while fetching video data: {e}")

def estimate_channel_earnings(channel_url):
    """Estimate total earnings for an entire channel."""
    youtube = get_service()
    channel_id = extract_channel_id(channel_url)
    try:
        # Fetch the list of videos from the channel
        video_list_response = youtube.search().list(part="id", channelId=channel_id, maxResults=10).execute()

        video_ids = [item["id"]["videoId"] for item in video_list_response["items"] if "videoId" in item["id"]]
        total_min, total_max = 0, 0

        for video_id in video_ids:
            response = youtube.videos().list(part="statistics", id=video_id).execute()
            if "items" in response and response['items']:
                stats = response["items"][0]["statistics"]
                view_count = int(stats.get('viewCount', 0))
                total_min += (view_count * 0.2) / 1000
                total_max += (view_count * 4.0) / 1000

        st.write(f"### Total Channel Earnings")
        st.write(f"Estimated Earnings Range: ${total_min:.2f} - ${total_max:.2f}")

        # Plot Total Earnings
        fig, ax = plt.subplots()
        ax.bar(["Min Earnings", "Max Earnings"], [total_min, total_max], color=["#ff4500", "#ffa07a"])
        plt.title("Channel Earnings Range")
        st.pyplot(fig)
    except HttpError as e:
        st.error("An error occurred while fetching channel data:")
        st.error(e)

def compare_channel_earnings(channel_urls):
    """Compare earnings across multiple channels."""
    youtube = get_service()
    data = []

    for channel_url in channel_urls:
        channel_id = extract_channel_id(channel_url)
        try:
            min_earnings, max_earnings = estimate_channel_earnings(channel_url)
            response = youtube.channels().list(part="snippet", id=channel_id).execute()
            if 'items' in response and response['items']:
                channel_name = response['items'][0]['snippet']['title']
                data.append({"Channel Name": channel_name, "Min Earnings": min_earnings, "Max Earnings": max_earnings})
        except HttpError as e:
            st.error(f"Failed to process channel {channel_url}: {e}")
            continue

    # Display Results
    df = pd.DataFrame(data)
    st.write("### Channel Comparison")
    st.dataframe(df)

    # Plot Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    df.plot(kind="bar", x="Channel Name", y=["Min Earnings", "Max Earnings"], ax=ax, color=["#ff4500", "#ffa07a"])
    plt.title("Earnings Comparison Across Channels")
    st.pyplot(fig)

# Main Options in Sidebar
options = [
    "Basic Video Analysis", "Channel Analysis", "YouTube Search", "Earnings Estimation", "Trending Keywords",
    "Content Strategy", "Trending Analysis", "Keyword Research", "Regional Content Strategy",
]

selected_option = st.sidebar.selectbox("Choose an option", options)

# Main Logic
if selected_option == "Earnings Estimation":
    st.write("## Earnings Estimation")

    # Submenu for Earnings Estimation
    earnings_options = ["Single Video Earnings", "Total Channel Earnings", "Compare Channels"]
    selected_earnings_option = st.selectbox("Choose an Earnings Estimation Type", earnings_options)

    if selected_earnings_option == "Single Video Earnings":
        video_url = st.text_input("Enter YouTube Video URL:")
        if st.button("Estimate Video Earnings"):
            estimate_video_earnings(video_url)

    elif selected_earnings_option == "Total Channel Earnings":
        channel_url = st.text_input("Enter YouTube Channel URL:")
        if st.button("Calculate Channel Earnings"):
            estimate_channel_earnings(channel_url)

    elif selected_earnings_option == "Compare Channels":
        channel_urls = st.text_area("Enter YouTube Channel URLs (one per line):").splitlines()
        if st.button("Compare Channels"):
            compare_channel_earnings(channel_urls)
