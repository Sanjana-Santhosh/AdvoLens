from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import numpy as np
import os
from app.core.ml_debug_log import add_ml_debug_log

# We use the standard base model - good balance of speed and accuracy
MODEL_NAME = "openai/clip-vit-base-patch32"


class ClipService:
    def __init__(self):
        print("Loading CLIP model... this might take a moment.")
        add_ml_debug_log(
            component="clip",
            operation="init",
            message="Loading CLIP model",
            details={"model_name": MODEL_NAME},
        )
        self.model = CLIPModel.from_pretrained(MODEL_NAME)
        self.processor = CLIPProcessor.from_pretrained(MODEL_NAME)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print(f"CLIP model loaded on {self.device}")
        add_ml_debug_log(
            component="clip",
            operation="init",
            message="CLIP model loaded",
            details={"model_name": MODEL_NAME, "device": self.device},
        )

    def get_embedding(self, image_path: str) -> np.ndarray | None:
        """
        Generates a 512-dim embedding vector for a given image file.
        """
        image_name = os.path.basename(image_path)
        add_ml_debug_log(
            component="clip",
            operation="get_embedding",
            message="Embedding generation started",
            details={"image": image_name},
        )
        try:
            image = Image.open(image_path)

            inputs = self.processor(images=image, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model.get_image_features(**inputs)

            embedding = outputs.cpu().numpy().flatten()
            norm = np.linalg.norm(embedding)
            normalized = embedding / norm if norm != 0 else embedding
            add_ml_debug_log(
                component="clip",
                operation="get_embedding",
                message="Embedding generation completed",
                details={
                    "image": image_name,
                    "vector_dim": int(normalized.shape[0]),
                    "normalized": bool(norm != 0),
                },
            )
            return normalized

        except Exception as e:
            print(f"Error generating embedding: {e}")
            add_ml_debug_log(
                component="clip",
                operation="get_embedding",
                level="ERROR",
                message="Embedding generation failed",
                details={"image": image_name, "error": str(e)},
            )
            return None


# Singleton instance to be reused
clip_service = ClipService()
