"""Scrape top-level comments from a YouTube video.

Uses the YouTube Data API v3 commentThreads endpoint to fetch
top-level comments for a given video.
"""

import os

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_youtube_service():
    """Build and return the YouTube Data API v3 client service."""
    return build("youtube", "v3", developerKey=API_KEY)


def fetch_comment_threads(youtube, video_id, max_results=100):
    """Fetch comment threads for a video via the commentThreads().list endpoint."""
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
    )
    return request.execute()


def main():
    youtube = get_youtube_service()
    video_id = input("Enter YouTube video ID: ").strip()
    response = fetch_comment_threads(youtube, video_id)
    print(f"Fetched {len(response.get('items', []))} comment threads")


if __name__ == "__main__":
    main()