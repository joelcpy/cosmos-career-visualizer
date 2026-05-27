from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
from core import generate_image

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR)
CORS(app)


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/style.css")
def styles():
    return send_from_directory(BASE_DIR, "style.css")


@app.route("/script.js")
def scripts():
    return send_from_directory(BASE_DIR, "script.js")


@app.route("/assets/<path:filename>")
def assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)


@app.route("/api/auth", methods=["POST"])
def auth():
    data = request.get_json()
    correct = os.getenv("SITE_PASSWORD", "")
    if correct and data.get("password") == correct:
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json()
    image_base64 = data.get("image_base64")
    raw_occupation = data.get("occupation", "professional")

    if not image_base64:
        return jsonify({"error": "No image provided"}), 400

    try:
        image_url, _ = generate_image(image_base64, raw_occupation)
        return jsonify({"image_url": image_url})
    except ValueError:
        return jsonify({"error": "blocked"}), 400
    except Exception as e:
        print(f"fal.ai error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG', 'false') == 'true', threaded=True)
