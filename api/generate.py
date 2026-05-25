from http.server import BaseHTTPRequestHandler
import json
import os
import fal_client

OCCUPATION_MAP = {
    "mermaid":   "marine biologist in a wetsuit",
    "merman":    "marine biologist in a wetsuit",
    "fairy":     "nature conservationist in green outdoor gear",
    "wizard":    "science professor in academic robes",
    "witch":     "chemistry teacher in a lab coat",
    "superhero": "search and rescue worker in a uniform",
    "princess":  "diplomat in formal attire",
    "prince":    "diplomat in formal attire",
    "ninja":     "martial arts instructor in a gi",
    "vampire":   "haematologist in a white lab coat",
    "zombie":    "special effects makeup artist",
    "pirate":    "ship captain in a naval uniform",
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


def sanitise(occupation: str):
    clean = occupation.strip().lower()
    for word in BLOCKED_WORDS:
        if word in clean:
            return None
    for key, replacement in OCCUPATION_MAP.items():
        if key in clean:
            return replacement
    return occupation.strip()


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"error": "Invalid request"})
            return

        image_base64 = body.get("image_base64")
        raw_occupation = body.get("occupation", "professional")

        if not image_base64:
            self._json(400, {"error": "No image provided"})
            return

        occupation = sanitise(raw_occupation)
        if occupation is None:
            self._json(400, {"error": "blocked"})
            return

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
            self._json(200, {"image_url": image_url})
        except Exception as e:
            print(f"fal.ai error: {e}")
            self._json(500, {"error": str(e)})

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        pass
