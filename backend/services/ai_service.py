import json
import os
from typing import Dict, Iterable, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
  raise RuntimeError("GEMINI_API_KEY is not set in the environment.")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-2.0-flash"

PROMPT = """
You are an expert aquaculture veterinary AI assistant.

You are analyzing up to THREE images of the SAME aquatic animal.

TASKS:
1. Identify species (fish or shrimp).
2. Determine if the animal appears diseased or healthy.
3. If diseased:
   - Predict most likely disease
   - Provide confidence score (0–100)
   - Explain visual reasoning
   - Infer severity (low, medium, high)
   - Suggest treatment approach
   - Suggest dosage per acre
4. If healthy:
   - State no disease detected
5. Never claim absolute certainty

OUTPUT STRICT JSON:

{
  "species": "",
  "health_status": "",
  "disease": {
    "name": "",
    "confidence": 0,
    "severity": ""
  },
  "reasoning": "",
  "treatment": {
    "approach": "",
    "dosage_per_acre": ""
  }
}

Return ONLY JSON.
""".strip()


def _build_image_parts(images: Iterable[Tuple[bytes, str]]):
  """Convert images to Gemini-compatible parts.

  images: iterable of (content_bytes, mime_type)
  """
  parts = []
  for idx, (content, mime_type) in enumerate(images):
    if idx >= 3:
      break
    if not content:
      continue
    parts.append(
        types.Part(
            inline_data=types.Blob(
                data=content,
                mime_type=mime_type or "image/jpeg",
            )
        )
    )
  return parts


def _parse_json_safely(text: str) -> Dict:
  """Parse JSON from model output with simple fallbacks."""
  text = text.strip()

  # Direct parse first
  try:
    return json.loads(text)
  except json.JSONDecodeError:
    pass

  # Try to extract from ```json ... ``` or ``` ... ```
  if "```" in text:
    segments = text.split("```")
    for segment in segments:
      segment = segment.strip()
      if not segment:
        continue
      # Remove optional 'json' language hint
      if segment.lower().startswith("json"):
        segment = segment[4:].strip()
      try:
        return json.loads(segment)
      except json.JSONDecodeError:
        continue

  # Fallback: try first {...} block
  start = text.find("{")
  end = text.rfind("}")
  if start != -1 and end != -1 and end > start:
    candidate = text[start : end + 1]
    try:
      return json.loads(candidate)
    except json.JSONDecodeError:
      pass

  raise ValueError("Model response is not valid JSON.")


def diagnose_aquatic_health(
    images: Iterable[Tuple[bytes, str]],
) -> Dict:
  """Run Gemini diagnosis and return structured JSON."""
  image_parts = _build_image_parts(images)

  user_content = types.Content(
      role="user",
      parts=[types.Part(text=PROMPT), *image_parts],
  )

  response = client.models.generate_content(
      model=MODEL_NAME,
      contents=[user_content],
  )

  if not response or not getattr(response, "text", None):
    raise ValueError("Empty response from Gemini model.")

  data = _parse_json_safely(response.text)

  # Ensure required top-level keys exist with defaults
  result: Dict = {
      "species": data.get("species", ""),
      "health_status": data.get("health_status", ""),
      "disease": {
          "name": "",
          "confidence": 0,
          "severity": "",
      },
      "reasoning": data.get("reasoning", ""),
      "treatment": {
          "approach": "",
          "dosage_per_acre": "",
      },
  }

  disease = data.get("disease") or {}
  if isinstance(disease, dict):
    result["disease"]["name"] = disease.get("name", "")
    try:
      result["disease"]["confidence"] = int(float(disease.get("confidence", 0)))
    except (TypeError, ValueError):
      result["disease"]["confidence"] = 0
    result["disease"]["severity"] = disease.get("severity", "")

  treatment = data.get("treatment") or {}
  if isinstance(treatment, dict):
    result["treatment"]["approach"] = treatment.get("approach", "")
    result["treatment"]["dosage_per_acre"] = treatment.get("dosage_per_acre", "")

  return result

