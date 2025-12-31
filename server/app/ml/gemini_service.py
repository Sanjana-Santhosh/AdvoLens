from google import genai
from google.genai import types
from PIL import Image
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize the client with API key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


class GeminiService:
    def __init__(self):
        self.model_name = "gemini-2.5-flash-lite"
        print("Gemini Vision service initialized")

    def analyze_image(self, image_path: str) -> dict:
        """
        Get both caption and tags from a single Gemini call.
        Returns: dict with 'caption' and 'tags' keys
        """
        try:
            # Read image as bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            
            # Determine mime type
            ext = image_path.lower().split(".")[-1]
            mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}
            mime_type = mime_map.get(ext, "image/jpeg")

            prompt = """Analyze this civic issue image and provide:
1. A brief description (one sentence, 15-20 words)
2. Relevant tags - MUST include the department name AND specific issue tags:

DEPARTMENT TAGS (include one of these):
- municipality: for garbage, sanitation, cleaning issues
- water_authority: for water, drainage, sewage issues  
- kseb: for electricity, streetlight, power issues
- pwd: for roads, potholes, infrastructure issues
- other: for anything else

ISSUE TAGS:
- Garbage: garbage, trash, dumping, waste, litter, illegal_dumping, overflowing_bin, plastic_waste, food_waste, street_litter
- Water: water, leak, pipe, sewage, drain, drainage, flooding, waterlogging, drainage_issue
- Electrical: light, pole, wire, electricity, power, streetlight, transformer, cable, broken_streetlight
- Roads: road, pothole, tar, pavement, bridge, highway, footpath, road_damage, broken_infrastructure
- Other: graffiti, abandoned_vehicle, stray_animal, encroachment, noise

Return ONLY a JSON object with this exact format:
{"caption": "description here", "tags": ["department_tag", "issue_tag1", "issue_tag2"]}

Example for garbage image:
{"caption": "Pile of plastic bottles and food wrappers scattered on street corner", "tags": ["municipality", "garbage", "street_litter", "plastic_waste"]}

Example for road issue:
{"caption": "Large pothole on main road causing traffic hazard", "tags": ["pwd", "pothole", "road_damage", "road"]}

Example for streetlight issue:
{"caption": "Broken streetlight pole leaning dangerously over sidewalk", "tags": ["kseb", "streetlight", "pole", "electrical"]}
"""

            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt),
                        ],
                    ),
                ],
            )

            # Parse JSON response - handle markdown code blocks
            text = response.text.strip()
            if text.startswith("```"):
                # Remove markdown code block markers
                lines = text.split("\n")
                text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
                text = text.strip()
            
            result = json.loads(text)
            return result

        except json.JSONDecodeError as e:
            print(f"Gemini JSON parse error: {e}, raw: {response.text}")
            return {"caption": "Unable to parse image analysis", "tags": ["other"]}
        except Exception as e:
            print(f"Gemini error: {e}")
            return {"caption": "Unable to analyze image", "tags": ["other"]}


# Singleton
gemini_service = GeminiService()
