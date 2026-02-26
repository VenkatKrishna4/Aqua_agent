from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from services.ai_service import diagnose_aquatic_health


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/styles.css", methods=["GET"])
def styles():
    return send_from_directory(FRONTEND_DIR, "styles.css")


@app.route("/script.js", methods=["GET"])
def script():
    return send_from_directory(FRONTEND_DIR, "script.js")


@app.route("/api/diagnose", methods=["POST"])
def diagnose():
    # Read uploaded images (max 3)
    if "images" in request.files:
        upload_files = request.files.getlist("images")
    else:
        upload_files = list(request.files.values())

    image_tuples = []
    for file_storage in upload_files[:3]:
        if not file_storage or not file_storage.filename:
            continue
        content = file_storage.read()
        if not content:
            continue
        mime_type = file_storage.mimetype or "image/jpeg"
        image_tuples.append((content, mime_type))

    # Read pond_size and pond_depth (not yet used in Gemini call)
    pond_size = request.form.get("pond_size")
    pond_depth = request.form.get("pond_depth")

    result = diagnose_aquatic_health(image_tuples)

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
