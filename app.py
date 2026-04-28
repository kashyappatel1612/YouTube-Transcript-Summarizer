import os
import re
from flask import Flask, request, jsonify, render_template
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Try to initialize API key initially
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def extract_video_id(url):
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

@app.route('/')
def index():
    return render_template('index.html', api_key_set=bool(os.getenv("GEMINI_API_KEY")))

@app.route('/api/configure', methods=['POST'])
def configure_api():
    data = request.json
    api_key = data.get('api_key')
    if api_key:
        genai.configure(api_key=api_key)
        # Update os environment temporarily
        os.environ["GEMINI_API_KEY"] = api_key
        # Save to .env for persistence
        with open('.env', 'w') as f:
            f.write(f"GEMINI_API_KEY={api_key}\n")
        return jsonify({"success": True, "message": "API key configured successfully!"})
    return jsonify({"success": False, "message": "API key is required."}), 400

@app.route('/api/summarize', methods=['POST'])
def summarize():
    if not os.getenv("GEMINI_API_KEY"):
        return jsonify({"success": False, "message": "Gemini API key is missing. Please configure it in settings."}), 400
        
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"success": False, "message": "URL is required"}), 400
        
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"success": False, "message": "Invalid YouTube URL"}), 400
        
    try:
        import yt_dlp
        import urllib.request
        import re
        
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en'],
            'quiet': True,
            'no_warnings': True,
        }
        
        transcript_text = ""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subs = info.get('subtitles', {})
            autos = info.get('automatic_captions', {})
            
            sub_url = None
            if subs and 'en' in subs:
                sub_url = next((f['url'] for f in subs['en'] if f.get('ext') == 'vtt' or 'fmt=vtt' in f['url']), None)
                if not sub_url and subs['en']: sub_url = subs['en'][0]['url']
            elif autos and 'en' in autos:
                sub_url = next((f['url'] for f in autos['en'] if f.get('ext') == 'vtt' or 'fmt=vtt' in f['url']), None)
                if not sub_url and autos['en']: sub_url = autos['en'][0]['url']
                
            if not sub_url:
                return jsonify({"success": False, "message": "No English transcript or auto-captions could be found for this video."}), 400
                
            req = urllib.request.Request(sub_url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            vtt_data = response.read().decode('utf-8')
            
            lines = vtt_data.split('\n')
            text_lines = []
            for line in lines:
                line = line.strip()
                if not line or line == 'WEBVTT' or '-->' in line or line.startswith('Kind:') or line.startswith('Language:') or line.startswith('Style:') or line.startswith('::cue'):
                    continue
                line = re.sub(r'<[^>]+>', '', line)
                if text_lines and text_lines[-1] == line:
                    continue
                text_lines.append(line)
            
            transcript_text = ' '.join(text_lines)
            
        if not transcript_text.strip():
            return jsonify({"success": False, "message": "Transcript was found but it is empty"}), 400
        
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Please provide a comprehensive summary of the following video transcript. Make it engaging, structure it with a brief overview, key points using bullet points, and a conclusion:\n\n{transcript_text[:100000]}"
        response = model.generate_content(prompt)
        
        return jsonify({"success": True, "summary": response.text, "video_id": video_id})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def translate():
    data = request.json
    text = data.get('text')
    target_lang = data.get('language')
    
    if not text or not target_lang:
        return jsonify({"success": False, "message": "Both text and target language are required"}), 400
        
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"Translate the following text to {target_lang}. Preserve all formatting (markdown, bullet points, headers):\n\n{text}"
        
        response = model.generate_content(prompt)
        
        return jsonify({"success": True, "translation": response.text})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
