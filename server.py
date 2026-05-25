from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import fal_client

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR)
CORS(app)

# Fantasy/creative occupations mapped to real-world equivalents
OCCUPATION_MAP = {
    "mermaid":     "marine biologist in a wetsuit",
    "merman":      "marine biologist in a wetsuit",
    "fairy":       "nature conservationist in green outdoor gear",
    "wizard":      "science professor in academic robes",
    "witch":       "chemistry teacher in a lab coat",
    "superhero":   "search and rescue worker in a uniform",
    "princess":    "diplomat in formal attire",
    "prince":      "diplomat in formal attire",
    "ninja":       "martial arts instructor in a gi",
    "vampire":     "haematologist in a white lab coat",
    "zombie":      "special effects makeup artist",
    "pirate":      "ship captain in a naval uniform",
}

BLOCKED_WORDS = {
    "stripper", "exotic dancer", "porn", "adult", "nude", "naked",
    "playboy", "onlyfans", "escort",
}

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


def sanitise(occupation: str) -> str:
    clean = occupation.strip().lower()

    # Block explicitly inappropriate inputs
    for word in BLOCKED_WORDS:
        if word in clean:
            return None

    # Remap fantasy occupations to safe real-world equivalents
    for key, replacement in OCCUPATION_MAP.items():
        if key in clean:
            return replacement

    return occupation.strip()


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
