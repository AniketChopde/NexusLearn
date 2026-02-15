from youtube_transcript_api import YouTubeTranscriptApi
import json

video_id = "bvQXI7-kMDw" # from user log

try:
    print("Attempting instantiation...")
    yta = YouTubeTranscriptApi()
    print("Instance created.")
    
    # Try fetch
    print(f"Calling fetch for {video_id}...")
    transcript = yta.fetch(video_id)
    print("Fetch returned object type:", type(transcript))
    print("Fetch result:", transcript)
    
except Exception as e:
    print(f"Error: {e}")
