import os
import time
from googleapiclient.discovery import build

# Set up YouTube Data API
api_key = 'AIzaSyCcHSKSMrDILV6Tq76lFWePQKsfx-8lv0E'  # Replace with your API key
youtube = build('youtube', 'v3', developerKey=api_key)

def get_video_tags(video_ids, test_mode=False):
    tags = {}
    total_videos = 10 if test_mode else len(video_ids)
    
    for i in range(0, total_videos, 50):
        batch_ids = video_ids[i:i+50]
        response = youtube.videos().list(
            part='snippet',
            id=','.join(batch_ids)
        ).execute()
        
        for item in response.get('items', []):
            video_id = item['id']
            video_tags = item['snippet'].get('tags', [])
            channel_title = item['snippet']['channelTitle']
            tags[video_id] = {'tags': video_tags, 'channel': channel_title}
            
        # Print progress
        print(f'Processed {i + len(batch_ids)} / {total_videos}')
        
        # To avoid hitting rate limits, you can add a delay
        time.sleep(1)
    
    return tags

# Read video IDs from file
with open('C:\\temp\\YTID.txt', 'r') as file:
    video_ids = [line.strip() for line in file.readlines()]

# Fetch tags (set test_mode to True to test with only 10 videos)
test_mode = False
video_tags = get_video_tags(video_ids, test_mode=test_mode)

# Save tags and channel names to a file
with open('video_tags.csv', 'w', encoding='utf-8') as file:
    file.write('video_id,channel,tags\n')
    for video_id, data in video_tags.items():
        tags = ','.join(data['tags'])
        channel = data['channel']
        file.write(f'{video_id},{channel},"{tags}"\n')

print('Tags extraction completed.')
