import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import locale

# Set the locale to format numbers as US dollars
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

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
        return channel_url.split("channel/")[-1]
    elif "youtube.com/c/" in channel_url or "youtube.com/user/" in channel_url:
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

        return total_min, total_max
    except HttpError as e:
        st.error(f"An error occurred while fetching data for {channel_url}: {e}")
        return None, None

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
                data.append({
                    "Channel Name": channel_name,
                    "Min Earnings (USD)": locale.currency(min_earnings, grouping=True),
                    "Max Earnings (USD)": locale.currency(max_earnings, grouping=True),
                    "Min Raw": min_earnings,  # For plotting
                    "Max Raw": max_earnings   # For plotting
                })
        except HttpError as e:
            st.error(f"Failed to process channel {channel_url}: {e}")
            continue

    # Display Results as a DataFrame
    df = pd.DataFrame(data)
    if not df.empty:
        st.write("### Channel Comparison")
        st.dataframe(df[["Channel Name", "Min Earnings (USD)", "Max Earnings (USD)"]])

        # Plot Comparison
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(
            kind="bar",
            x="Channel Name",
            y=["Min Raw", "Max Raw"],
            ax=ax,
            color=["#ff4500", "#ffa07a"]
        )
        ax.set_ylabel("Earnings (USD)")
        plt.title("Earnings Comparison Across Channels")
        st.pyplot(fig)

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

    earnings_options = ["Single Channel Earnings", "Compare Multiple Channels"]
    selected_earnings_option = st.selectbox("Choose an Earnings Type", earnings_options)

    if selected_earnings_option == "Single Channel Earnings":
        channel_url = st.text_input("Enter YouTube Channel URL:")
        if st.button("Calculate Channel Earnings"):
            min_earnings, max_earnings = estimate_channel_earnings(channel_url)
            if min_earnings is not None:
                st.write(f"### Estimated Earnings Range")
                st.write(f"{locale.currency(min_earnings, grouping=True)} - {locale.currency(max_earnings, grouping=True)}")

    elif selected_earnings_option == "Compare Multiple Channels":
        channel_urls = st.text_area("Enter YouTube Channel URLs (one per line):").splitlines()
        if st.button("Compare Channels"):
            compare_channel_earnings(channel_urls)
