import os
import pandas as pd
from datetime import datetime, timedelta
import googleapiclient.discovery
from googleapiclient.errors import HttpError
import time


def get_youtube_service(api_key):
    """Initialize the YouTube API client."""
    return googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)


def get_date_range(days_ago=1):
    """Get the start and end datetime strings for a specific day ago."""
    target_date = datetime.now() - timedelta(days=days_ago)
    start = target_date.strftime('%Y-%m-%dT00:00:00Z')
    end = target_date.strftime('%Y-%m-%dT23:59:59Z')
    return start, end


def fetch_new_channel_ids(youtube, start_date, end_date, retries=3):
    """Fetch newly created channel IDs from YouTube."""
    channel_ids = []
    next_page_token = None

    while True:
        try:
            response = youtube.search().list(
                part='id',
                type='channel',
                q='',
                order='relevance',
                maxResults=50,  # keeping it 50 to be safer with quota
                publishedAfter=start_date,
                publishedBefore=end_date,
                pageToken=next_page_token
            ).execute()

            for item in response.get('items', []):
                channel_id = item['id']['channelId']
                channel_ids.append({'channelid': channel_id})

            next_page_token = response.get('nextPageToken')

            if not next_page_token:
                break

        except HttpError as e:
            if retries > 0:
                print(f"HttpError occurred: {e}. Retrying in 5 seconds...")
                time.sleep(5)
                retries -= 1
                continue
            else:
                print(f"Failed after retries. Error: {e}")
                break

    return channel_ids


def save_channels_to_csv(channel_ids, filename='newchannels.csv'):
    """Save channel IDs to a CSV file."""
    df = pd.DataFrame(channel_ids)
    df.to_csv(filename, index=False)
    print(f"Saved {len(df)} channels to {filename}")
    print(df)


def main():
    # Get API key safely
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("Missing YOUTUBE_API_KEY environment variable!")

    youtube = get_youtube_service(api_key)
    start_date, end_date = get_date_range()

    channel_ids = fetch_new_channel_ids(youtube, start_date, end_date)

    if channel_ids:
        save_channels_to_csv(channel_ids)
    else:
        print("No new channels found.")


if __name__ == "__main__":
    main()

