from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/index', methods=['GET', 'POST'])
@app.route('/download', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/download/<path:path>', methods=['GET', 'POST'])
def handler(path=''):
    return jsonify({"status": "ok", "message": "Backend operativo"})

if __name__ == '__main__':
    app.run()