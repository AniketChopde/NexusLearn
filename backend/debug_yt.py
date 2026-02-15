from youtube_transcript_api import YouTubeTranscriptApi
import youtube_transcript_api
print(f"Version: {youtube_transcript_api.__version__ if hasattr(youtube_transcript_api, '__version__') else 'unknown'}")
print(f"File: {youtube_transcript_api.__file__}")
print(f"Dir: {dir(YouTubeTranscriptApi)}")
try:
    print(YouTubeTranscriptApi.get_transcript)
except AttributeError as e:
    print(e)
