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

MODERATION_SYSTEM = """You are a content safety filter AND image prompt writer for a school career day app for children aged 10–16.

A child has typed the career they want to be. Their face photo will be used as a reference to generate a photorealistic image of them in that career.

Rules — apply in order:
1. BLOCK if the input is sexual, violent, drug-related, or clearly inappropriate for children → {"ok": false}
2. For ALL other careers — real or fantasy (princess, knight, wizard, mermaid, superhero, pirate, etc.) — write a vivid fal.ai image prompt that:
   - Places the person in the ideal costume/attire for that career
   - Puts them in a fitting, atmospheric environment (palace throne room for princess, enchanted forest for witch, etc.)
   - Is fully clothed and appropriate for children
   - Is photorealistic, cinematic, highly detailed — NOT cartoon or anime
   - Is exciting so the child is wowed seeing themselves in it

Respond with ONLY valid JSON, no extra text:
{"ok": true, "occupation": "<cleaned-up career name>", "prompt": "<vivid fal.ai prompt, 40-70 words>"}
or
{"ok": false}"""

NEGATIVE_PROMPT = (
    "plain background, black background, grey background, white background, "
    "studio background, blank background, isolated, cutout, no background, "
    "cartoon, anime, illustration, drawing, painting, cgi, render, 3d render, "
    "disney, pixar, dreamworks, animated movie, cartoon character, "
    "unrealistic, fake, doll, plastic skin, smooth skin, airbrushed, "
    "child, kid, young, baby face, "
    "revealing clothing, bikini, swimwear, underwear, lingerie, "
    "low cut, cleavage, nsfw, adult content, suggestive, "
    "sexy, seductive, bare skin, shirtless"
)


def get_occupation_and_prompt(raw_occupation: str):
    """Returns (occupation, prompt) or (None, None) if blocked."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        occ = raw_occupation.strip()
        prompt = (
            f"A person dressed as a {occ}, standing in a fitting environment for a {occ}, "
            "RAW photo, photorealistic, hyperrealistic face, sharp facial features, "
            "true-to-life skin texture, natural cinematic lighting, vivid detailed background, 8k, high detail, live action"
        )
        return occ, prompt

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=MODERATION_SYSTEM,
            messages=[{"role": "user", "content": raw_occupation.strip()}],
        )
        result = json.loads(msg.content[0].text)
        if result.get("ok") is False:
            return None, None
        occupation = result.get("occupation", raw_occupation.strip())
        fal_prompt = result.get("prompt", f"A {occupation}, photorealistic, 8k")
        fal_prompt += (
            ", RAW photo, photorealistic, hyperrealistic face, sharp facial features, "
            "true-to-life skin texture, natural cinematic lighting, 8k, high detail, live action"
        )
        return occupation, fal_prompt
    except Exception:
        occ = raw_occupation.strip()
        prompt = (
            f"A person dressed as a {occ}, standing in a fitting environment for a {occ}, "
            "RAW photo, photorealistic, hyperrealistic face, sharp facial features, "
            "true-to-life skin texture, natural cinematic lighting, vivid detailed background, 8k, high detail, live action"
        )
        return occ, prompt


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

    occupation, prompt = get_occupation_and_prompt(raw_occupation)
    if occupation is None:
        return jsonify({"error": "blocked"}), 400

    try:
        result = fal_client.run(
            "fal-ai/flux-pulid",
            arguments={
                "prompt": prompt,
                "negative_prompt": NEGATIVE_PROMPT,
                "reference_image_url": f"data:image/jpeg;base64,{image_base64}",
                "num_inference_steps": 28,
                "guidance_scale": 6.5,
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
