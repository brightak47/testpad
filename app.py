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

def extract_channel_id(channel_url):
    """Extract the channel ID from a YouTube channel URL, including @handles."""
    youtube = get_service()

    if "youtube.com/channel/" in channel_url:
        # Standard channel URL
        return channel_url.split("channel/")[-1]
    elif "youtube.com/c/" in channel_url or "youtube.com/user/" in channel_url:
        # Custom URL (c/User)
        custom_name = channel_url.split("/")[-1]
        try:
            response = youtube.channels().list(
                part="id",
                forUsername=custom_name
            ).execute()
            if 'items' in response and response['items']:
                return response['items'][0]['id']
            else:
                st.error("Failed to resolve the custom URL to a channel ID.")
                st.stop()
        except Exception as e:
            st.error(f"An error occurred while resolving the custom URL: {e}")
            st.stop()
    elif "youtube.com/@" in channel_url:
        # Handle @username URLs
        handle = channel_url.split("@")[-1]
        try:
            response = youtube.search().list(
                part="snippet",
                q=f"@{handle}",
                type="channel",
                maxResults=1
            ).execute()
            if 'items' in response and response['items']:
                return response['items'][0]['snippet']['channelId']
            else:
                st.error("Failed to resolve the handle to a channel ID.")
                st.stop()
        except Exception as e:
            st.error(f"An error occurred while resolving the handle: {e}")
            st.stop()
    else:
        st.error("Invalid channel URL. Please provide a valid YouTube channel URL.")
        st.stop()

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

# Sidebar: API Key Input
st.sidebar.write("## API Configuration")
st.sidebar.text_input(
    "Enter YouTube API Key:",
    type="password",
    key="api_key",
    help="Enter your YouTube API key to enable functionality.",
)

# Main Options in Sidebar
options = [
    "Basic Video Analysis", "Channel Analysis", "Earnings Estimation"
]

selected_option = st.sidebar.selectbox("Choose an option", options)

# Main Logic
if selected_option == "Earnings Estimation":
    st.write("## Earnings Estimation")

    # Channel URL Input
    channel_url = st.text_input("Enter YouTube Channel URL:")
    if st.button("Calculate Channel Earnings"):
        estimate_channel_earnings(channel_url)
