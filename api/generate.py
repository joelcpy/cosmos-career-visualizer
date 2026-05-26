from http.server import BaseHTTPRequestHandler
import json
import os
import fal_client
import anthropic

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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        occ = raw_occupation.strip()
        prompt = (
            f"A person dressed as a {occ}, standing in a fitting environment for a {occ}, "
            "RAW photo, real human being, not cartoon, not animated, not 3d render, "
            "photorealistic, hyperrealistic face, sharp facial features, "
            "true-to-life skin texture, natural cinematic lighting, vivid detailed background, 8k, high detail"
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
        # Always append quality boosters
        fal_prompt += (
            ", RAW photo, real human being, not cartoon, not animated, not 3d render, "
            "photorealistic, hyperrealistic face, sharp facial features, "
            "true-to-life skin texture, natural cinematic lighting, 8k, high detail"
        )
        return occupation, fal_prompt
    except Exception:
        occ = raw_occupation.strip()
        prompt = (
            f"A person dressed as a {occ}, standing in a fitting environment for a {occ}, "
            "RAW photo, real human being, not cartoon, not animated, not 3d render, "
            "photorealistic, hyperrealistic face, sharp facial features, "
            "true-to-life skin texture, natural cinematic lighting, vivid detailed background, 8k, high detail"
        )
        return occ, prompt


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

        occupation, prompt = get_occupation_and_prompt(raw_occupation)
        if occupation is None:
            self._json(400, {"error": "blocked"})
            return

        try:
            result = fal_client.run(
                "fal-ai/flux-pulid",
                arguments={
                    "prompt": prompt,
                    "negative_prompt": NEGATIVE_PROMPT,
                    "reference_image_url": f"data:image/jpeg;base64,{image_base64}",
                    "num_inference_steps": 28,
                    "guidance_scale": 6.5,
                    "id_weight": 0.7,
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
