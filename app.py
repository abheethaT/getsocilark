from flask import Flask, render_template_string, request, send_file, after_this_request
import yt_dlp
import os
import time

app = Flask(__name__)

DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Helper: Creates a temporary cookie file from Koyeb Environment Variables
def get_cookie_path():
    cookie_content = os.environ.get('YOUTUBE_COOKIES')
    if cookie_content:
        path = 'temp_cookies.txt'
        with open(path, 'w') as f:
            f.write(cookie_content)
        return path
    return None

UI_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediaFlow Pro | Fix</title>
    <style>
        :root { --accent: #ff0050; --bg: #0a0a0c; --glass: rgba(255, 255, 255, 0.05); }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: white; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
        .app-card { background: var(--glass); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.1); border-radius: 32px; width: 100%; max-width: 500px; padding: 30px; text-align: center; }
        .search-box { background: rgba(0,0,0,0.3); border-radius: 18px; padding: 6px; display: flex; border: 1px solid rgba(255,255,255,0.1); }
        .search-box input { flex: 1; background: transparent; border: none; padding: 15px; color: white; outline: none; }
        .search-box button { background: var(--accent); color: white; border: none; padding: 0 20px; border-radius: 14px; font-weight: bold; cursor: pointer; }
        .tabs { display: flex; gap: 5px; margin: 25px 0 15px 0; background: rgba(255,255,255,0.03); padding: 5px; border-radius: 14px; }
        .tab-btn { flex: 1; padding: 10px; border-radius: 10px; background: transparent; color: #888; border: none; cursor: pointer; font-weight: bold; font-size: 12px; }
        .tab-btn.active { background: white; color: black; }
        .tab-pane { display: none; }
        .tab-pane.active { display: block; animation: fadeIn 0.3s; }
        .dl-btn { width: 100%; padding: 15px; background: var(--accent); color: white; border: none; border-radius: 12px; font-weight: 800; cursor: pointer; margin-top: 10px; }
        .loader { display: none; margin: 20px auto; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--accent); border-radius: 50%; width: 25px; height: 25px; animation: spin 0.8s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
</head>
<body>
    <div class="app-card">
        <h2>Media<span>Flow</span> Fix</h2>
        <form action="/get_info" method="post" onsubmit="showLoading()">
            <div class="search-box">
                <input type="text" name="url" placeholder="Paste link here..." value="{{ url if url else '' }}" required>
                <button type="submit">Analyze</button>
            </div>
        </form>
        <div id="loader" class="loader"></div>
        {% if info %}
        <div style="margin-top:20px;">
            <img src="{{ info.thumbnail }}" style="width:100%; border-radius:15px;">
            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab(event, 'all')">ALL</button>
                <button class="tab-btn" onclick="switchTab(event, 'video')">VIDEO</button>
                <button class="tab-btn" onclick="switchTab(event, 'audio')">AUDIO</button>
            </div>
            {% set panes = [('all', info.all_f), ('video', info.video_f), ('audio', info.audio_f)] %}
            {% for id, formats in panes %}
            <div id="{{ id }}" class="tab-pane {{ 'active' if id == 'all' else '' }}">
                <form action="/download" method="post" onsubmit="showLoading()">
                    <input type="hidden" name="url" value="{{ info.url }}">
                    <select name="format_id" style="width:100%; padding:10px; border-radius:10px; background:#111; color:white; border:1px solid #333;">
                        {% for f in formats %}<option value="{{ f.id }}">{{ f.ext|upper }} - {{ f.res }} ({{ f.size }})</option>{% endfor %}
                    </select>
                    <button type="submit" class="dl-btn">Start Download</button>
                </form>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    <script>
        function showLoading() { document.getElementById('loader').style.display = 'block'; }
        function switchTab(evt, id) {
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(id).classList.add('active');
            evt.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(UI_HTML)

@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    cookie_path = get_cookie_path()
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True, 
        'noplaylist': True,
        'cookiefile': cookie_path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            meta = ydl.extract_info(url, download=False)
            all_f, video_f, audio_f = [], [], []
            for f in meta.get('formats', []):
                size = f.get('filesize') or f.get('filesize_approx') or 0
                size_str = f"{size / (1024*1024):.1f} MB" if size > 0 else "---"
                f_data = {'id': f['format_id'], 'ext': f['ext'], 'res': f.get('format_note') or f.get('resolution') or 'N/A', 'size': size_str}
                if f.get('vcodec') == 'none': audio_f.append(f_data)
                elif f.get('acodec') != 'none':
                    all_f.append(f_data)
                    if f['ext'] == 'webm' or (f.get('height') and f.get('height') <= 720): video_f.append(f_data)
            return render_template_string(UI_HTML, info={'title': meta['title'], 'thumbnail': meta['thumbnail'], 'url': url, 'all_f': all_f[::-1], 'video_f': video_f, 'audio_f': audio_f[::-1]}, url=url)
        except Exception as e: return f"Error: {str(e)}"
        finally:
            if cookie_path and os.path.exists(cookie_path): os.remove(cookie_path)

@app.route('/download', methods=['POST'])
def download():
    url, fid = request.form.get('url'), request.form.get('format_id')
    cookie_path = get_cookie_path()
    unique_name = f"video_{int(time.time())}"
    ydl_opts = {
        'format': f'{fid}+bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{unique_name}.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'cookiefile': cookie_path
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)

    @after_this_request
    def cleanup(response):
        try:
            if os.path.exists(file_path): os.remove(file_path)
            if cookie_path and os.path.exists(cookie_path): os.remove(cookie_path)
        except: pass
        return response

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
