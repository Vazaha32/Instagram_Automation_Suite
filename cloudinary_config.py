import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


def upload_image(file):
    """
    Prend un fichier image (jpg/png) et le téléverse sur Cloudinary.
    """
    # file peut être un PathLike, un bytes ou un file-like
    return cloudinary.uploader.upload(
        file,
        resource_type="image"
    )["secure_url"]


def upload_video(file):
    """
    Prend un fichier vidéo (mp4) et le téléverse sur Cloudinary.
    """
    return cloudinary.uploader.upload(
        file,
        resource_type="video"
    )["secure_url"]
