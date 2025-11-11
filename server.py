from flask import Flask, request, send_file, render_template_string, Response
import subprocess
import tempfile
import os
import glob
import shutil
import time
import threading

app = Flask(__name__)

ALLOWED_SITES = [
    "youtube.com", "youtu.be",
    "tiktok.com", "vt.tiktok.com",
    "instagram.com", "www.instagram.com",
    "twitter.com", "x.com"
]

DOWNLOADS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<title>Video Downloader</title>
<style>
body {
  font-family: Arial, sans-serif;
  background: linear-gradient(135deg, #1c1c1c, #2b2b2b);
  color: #f3f3f3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  margin: 0;
}
.container {
  background: #2e2e2e;
  padding: 30px 40px;
  border-radius: 15px;
  box-shadow: 0 0 20px rgba(0,0,0,0.5);
  text-align: center;
  width: 90%;
  max-width: 500px;
}
h1 {
  margin-bottom: 20px;
  color: #00e676;
}
input[type="text"] {
  width: 100%;
  padding: 12px;
  border: none;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 16px;
}
select {
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  border: none;
  font-size: 16px;
  margin-bottom: 20px;
}
button {
  background: #00e676;
  color: #1c1c1c;
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: 0.3s;
  width: 100%;
}
button:hover {
  background: #00c853;
}
footer {
  margin-top: 25px;
  font-size: 13px;
  color: #bbb;
}
</style>
</head>
<body>
  <div class="container">
    <h1>🎬 Video Downloader</h1>
    <form method="post" action="/download">
      <input type="text" name="url" placeholder="Tempelkan link YouTube / TikTok / Instagram" required>
      <select name="format_choice">
        <option value="mp4" selected>Download sebagai MP4 (Video)</option>
        <option value="mp3">Download sebagai MP3 (Audio)</option>
      </select>
      <button type="submit">Download</button>
    </form>
    <footer>© Najidla Azman</footer>
  </div>
</body>
</html>
"""

def allowed_url(url: str):
    return any(site in url for site in ALLOWED_SITES)

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_PAGE)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()
    format_choice = request.form.get("format_choice", "mp4")

    if not url or not allowed_url(url):
        return "URL tidak valid atau situs belum didukung.", 400

    workdir = tempfile.mkdtemp(prefix="ydl_", dir=DOWNLOADS_DIR)
    output_template = os.path.join(workdir, "%(title)s.%(ext)s")

    # Pilih command sesuai format
    if format_choice == "mp3":
        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", output_template,
            url
        ]
    else:
        cmd = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio/best",
            "-o", output_template,
            "--merge-output-format", "mp4",
            url
        ]

    try:
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if process.returncode != 0:
            return Response(f"Gagal mendownload:\n\n{process.stderr}", mimetype="text/plain", status=500)

        files = glob.glob(os.path.join(workdir, "*"))
        if not files:
            return "Gagal menemukan file hasil download.", 500

        filepath = max(files, key=os.path.getctime)
        filename = os.path.basename(filepath)
        return send_file(filepath, as_attachment=True, download_name=filename)

    except subprocess.TimeoutExpired:
        return "Proses download terlalu lama (timeout).", 500
    except Exception as e:
        return f"Terjadi error: {e}", 500
    finally:
        def delayed_clean():
            try:
                time.sleep(5)
                shutil.rmtree(workdir, ignore_errors=True)
            except:
                pass
        threading.Thread(target=delayed_clean, daemon=True).start()

if __name__ == "__main__":
    print("Server jalan di http://127.0.0.1:5000")
    print("Pastikan sudah install yt-dlp & flask → pip install yt-dlp flask")
    app.run(host="127.0.0.1", port=5000, debug=False)
