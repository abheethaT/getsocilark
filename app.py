import os

# Function ekak hadaganna cookies file eka create karaganna
def create_cookies_file():
    cookie_content = os.environ.get('YOUTUBE_COOKIES', '')
    if cookie_content:
        with open('cookies.txt', 'w') as f:
            f.write(cookie_content)
        return 'cookies.txt'
    return None

# --- get_info function eka athule ---
@app.route('/get_info', methods=['POST'])
def get_info():
    url = request.form.get('url')
    cookie_path = create_cookies_file() # Cookies file eka hadagannawa
    
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True, 
        'noplaylist': True,
        'cookiefile': cookie_path if cookie_path else None # Methanata add karanna
    }
    # ... ithuru code eka ...

# --- download function eka athule ---
@app.route('/download', methods=['POST'])
def download():
    url, fid = request.form.get('url'), request.form.get('format_id')
    cookie_path = create_cookies_file()
    
    unique_name = f"video_{int(time.time())}"
    ydl_opts = {
        'format': f'{fid}+bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/{unique_name}.%(ext)s',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'cookiefile': cookie_path if cookie_path else None # Methanatath add karanna
    }
    # ... ithuru code eka ...
