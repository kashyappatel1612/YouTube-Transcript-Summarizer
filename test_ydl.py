import yt_dlp
import sys
import json
import re

URL = sys.argv[1]

ydl_opts = {
    'skip_download': True,
    'writesubtitles': True,
    'writeautomaticsub': True,
    'subtitleslangs': ['en'],
    'quiet': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(URL, download=False)
    
    # Check manual and auto subs
    subs = info.get('subtitles', {})
    autos = info.get('automatic_captions', {})
    
    sub_url = None
    if subs and 'en' in subs:
        sub_url = next((f['url'] for f in subs['en'] if f['ext'] == 'vtt'), None)
    elif autos and 'en' in autos:
        sub_url = next((f['url'] for f in autos['en'] if f['ext'] == 'vtt'), None)
        
    print(f"Subtitle URL: {sub_url}")
    
    if sub_url:
        import urllib.request
        response = urllib.request.urlopen(sub_url)
        vtt_data = response.read().decode('utf-8')
        
        # Clean up VTT to text
        lines = vtt_data.split('\n')
        text = []
        for line in lines:
            line = line.strip()
            # Skip empty lines, WebVTT header, timestamps, and style tags
            if not line or line == 'WEBVTT' or '-->' in line or line.startswith('Kind:') or line.startswith('Language:') or line.startswith('Style:') or line.startswith('::cue'):
                continue
            # Remove VTT inline tags (e.g. <c>, </c>, <00:00:01.000>)
            line = re.sub(r'<[^>]+>', '', line)
            # Avoid repeating exactly the same lines due to VTT scrolling
            if text and text[-1] == line:
                continue
            text.append(line)
        
        transcript_text = ' '.join(text)
        print("Length of cleaned transcript:", len(transcript_text))
        print("Sample:", transcript_text[:500])
    else:
        print("No English subtitles found")
