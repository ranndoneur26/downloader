import os
import tempfile
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

@app.route('/download/<format_type>', methods=['POST'])
def download(format_type):
    data = request.get_json(silent=True) or {}
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL no proporcionada'}), 400

    temp_dir = tempfile.gettempdir()

    if format_type == 'audio':
        # Descarga la mejor pista de audio directa (m4a/aac) sin requerir conversión ffmpeg a mp3
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
    else:
        # Descarga un stream único que combina vídeo y audio sin requerir ffmpeg
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            title = info.get('title', 'descarga')
            ext = info.get('ext', 'mp4' if format_type == 'video' else 'm4a')
            download_name = f"{title}.{ext}"

        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return jsonify({'error': 'El archivo descargado está vacío'}), 500

        return send_file(
            filepath,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500