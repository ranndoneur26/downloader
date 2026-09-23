import os
import tempfile
from flask import Flask, request, jsonify, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

def get_base_ydl_opts(temp_dir):
    opts = {
        'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        # Evita el bloqueo "Sign in to confirm you're not a bot" en IPs de datacenter
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios']
            }
        },
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/123.0.0.0 Safari/537.36'
            )
        }
    }

    # Soporte opcional para cookies via variable de entorno en Vercel
    cookies_env = os.environ.get('YOUTUBE_COOKIES')
    if cookies_env:
        cookie_file_path = os.path.join(temp_dir, 'cookies.txt')
        with open(cookie_file_path, 'w', encoding='utf-8') as f:
            f.write(cookies_env)
        opts['cookiefile'] = cookie_file_path

    return opts

@app.route('/download/<format_type>', methods=['POST'])
def download(format_type):
    data = request.get_json(silent=True) or {}
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL no proporcionada.'}), 400

    temp_dir = tempfile.gettempdir()
    ydl_opts = get_base_ydl_opts(temp_dir)

    if format_type == 'audio':
        # Selecciona el mejor audio directo (m4a/aac) sin exigir recodificación con ffmpeg
        ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'
    else:
        # Selecciona un stream que ya integre audio y vídeo para no necesitar mezcla con ffmpeg
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)
            title = info.get('title', 'descarga')
            ext = info.get('ext', 'mp4' if format_type == 'video' else 'm4a')
            download_name = f"{title}.{ext}"

        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            return jsonify({'error': 'No se pudo generar el archivo de vídeo/audio.'}), 500

        # Elimina el archivo de /tmp después de enviarlo al cliente para no saturar memoria/disco
        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass
            return response

        return send_file(
            filepath,
            as_attachment=True,
            download_name=download_name
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()