import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


def upload_image(file_path: str) -> str:
    """Upload image to Cloudinary and return public URL"""
    try:
        result = cloudinary.uploader.upload(file_path, folder="advolens")
        return result['secure_url']  # Returns full URL
    except Exception as e:
        print(f"Cloudinary upload failed: {e}")
        return None
