from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
import fal_client
import anthropic

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR)
CORS(app)

MODERATION_SYSTEM = """You are a content safety filter for a school career day app used by children aged 10–16.

A child has typed the career they want to be. Evaluate it and respond with JSON only.

Rules — apply in order:
1. BLOCK if the input is sexual, violent, drug-related, weapon-related, or otherwise clearly inappropriate for children. Respond: {"ok": false}
2. SAFETY-GUARD if the career could plausibly produce revealing or sexualised imagery (e.g. swimsuit model, bikini model, exotic dancer, burlesque performer) → keep the career but append "in professional attire, fully clothed" to the occupation string.
3. PASS everything else as-is — including fantasy / fictional roles like knight, wizard, witch, mermaid, superhero, pirate, ninja, vampire, fairy, dragon rider, etc. These are fun and intentional. Just clean up capitalisation and phrasing lightly.

Respond with ONLY valid JSON, no extra text:
{"ok": true, "occupation": "<occupation string>"}
or
{"ok": false}"""

NEGATIVE_PROMPT = (
    "plain background, black background, grey background, white background, "
    "studio background, blank background, isolated, cutout, no background, "
    "cartoon, anime, illustration, drawing, painting, cgi, render, "
    "unrealistic, fake, doll, plastic skin, smooth skin, "
    "child, kid, young, baby face, "
    "revealing clothing, bikini, swimwear, underwear, lingerie, "
    "low cut, cleavage, nsfw, adult content, suggestive, "
    "sexy, seductive, bare skin, shirtless"
)


def sanitise(raw_occupation: str):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return raw_occupation.strip()

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system=MODERATION_SYSTEM,
            messages=[{"role": "user", "content": raw_occupation.strip()}],
        )
        result = json.loads(msg.content[0].text)
        if result.get("ok") is False:
            return None
        return result.get("occupation", raw_occupation.strip())
    except Exception:
        return raw_occupation.strip()


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

    occupation = sanitise(raw_occupation)
    if occupation is None:
        return jsonify({"error": "blocked"}), 400

    prompt = (
        f"A person working as a {occupation}, "
        f"standing in a detailed realistic {occupation} workplace environment, "
        "relevant props and setting clearly visible in the background, "
        "half body shot, wearing appropriate professional work attire, "
        "photorealistic, hyperrealistic face, sharp facial features, "
        "true-to-life skin texture, natural cinematic lighting, "
        "vivid detailed background, 8k, high detail"
    )

    try:
        result = fal_client.run(
            "fal-ai/flux-pulid",
            arguments={
                "prompt": prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "reference_image_url": f"data:image/jpeg;base64,{image_base64}",
                "num_inference_steps": 20,
                "guidance_scale": 4.0,
                "num_images": 1,
            },
        )
        image_url = result["images"][0]["url"]
        return jsonify({"image_url": image_url})

    except Exception as e:
        print(f"fal.ai error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_DEBUG','false')=='true', threaded=True)
