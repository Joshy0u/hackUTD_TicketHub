from bottle import route, run, request
from pathlib import Path
from datetime import datetime

@route('/upload', method='POST')
def upload():
    upload = request.files.get('file')
    hostname = request.forms.get('hostname', 'unknown')
    timestamp = request.forms.get('timestamp', datetime.utcnow().strftime('%Y%m%d_%H%M%S'))

    dest_dir = Path('received_logs')
    dest_dir.mkdir(exist_ok=True)
    filename = f"{hostname}_{timestamp}_{upload.filename}"
    path = dest_dir / filename
    upload.save(path)

    print(f"[recv] {path} ({path.stat().st_size} bytes)")
    return {"status": "ok", "saved_as": filename}

run(host='0.0.0.0', port=8000)
