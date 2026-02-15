import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi
print(f"Package File: {youtube_transcript_api.__file__}")
print(f"Class: {YouTubeTranscriptApi}")
print(f"Dir Class: {dir(YouTubeTranscriptApi)}")
try:
    print(f"Attr: {YouTubeTranscriptApi.get_transcript}")
except AttributeError:
    print("No get_transcript")
