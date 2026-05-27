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
   - Wears the authentic uniform or attire for that career (sports uniforms, armour, costumes are all fine) — no nudity, swimwear, or underwear
   - Is photorealistic, cinematic, highly detailed — NOT cartoon or anime
   - Is exciting so the child is wowed seeing themselves in it
   - NEVER mention gender, sex, or pronouns (no man/woman/boy/girl/he/she/him/her/male/female) — the reference photo already carries the person's appearance and gender
   - Choose the most exciting framing: use "full body shot" for careers where the costume/action matters (astronaut, firefighter, knight, dancer, athlete, superhero, etc.); use "upper body portrait" for careers where the face and setting tell the story (doctor, scientist, chef, teacher, etc.)

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
    "bikini, swimwear, underwear, lingerie, "
    "low cut, cleavage, nsfw, adult content, suggestive, "
    "sexy, seductive, shirtless, exposed chest, exposed midriff"
)

QUALITY_SUFFIX = (
    ", RAW photo, real human being, not cartoon, not animated, not 3d render, "
    "photorealistic, hyperrealistic face, sharp facial features, "
    "true-to-life skin texture, natural cinematic lighting, 8k, high detail"
)


def get_occupation_and_prompt(raw_occupation: str):
    """Returns (occupation, prompt) or (None, None) if blocked."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    occ = raw_occupation.strip()

    if not api_key:
        return occ, f"A person dressed as a {occ}, standing in a fitting environment for a {occ}{QUALITY_SUFFIX}, vivid detailed background"

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=MODERATION_SYSTEM,
            messages=[{"role": "user", "content": occ}],
        )
        result = json.loads(msg.content[0].text)
        if result.get("ok") is False:
            return None, None
        occupation = result.get("occupation", occ)
        prompt = result.get("prompt", f"A {occupation}, photorealistic, 8k") + QUALITY_SUFFIX
        return occupation, prompt
    except Exception:
        return occ, f"A person dressed as a {occ}, standing in a fitting environment for a {occ}{QUALITY_SUFFIX}, vivid detailed background"


def generate_image(image_base64: str, raw_occupation: str):
    """Returns (image_url, occupation) or raises an exception if blocked/failed."""
    occupation, prompt = get_occupation_and_prompt(raw_occupation)
    if occupation is None:
        raise ValueError("blocked")

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
    return result["images"][0]["url"], occupation
