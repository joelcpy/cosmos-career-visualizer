from http.server import BaseHTTPRequestHandler
import json
import os
import fal_client
import anthropic

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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
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
