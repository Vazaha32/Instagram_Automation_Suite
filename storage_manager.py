import cloudinary
import dropbox
import os
from dotenv import load_dotenv

load_dotenv()


class StorageManager:
    def __init__(self):
        self.mode = os.getenv("STORAGE_MODE", "local")
        if self.mode == "local":
            os.makedirs("media", exist_ok=True)  # <-- Crée le dossier

        if self.mode == "cloudinary":
            cloudinary.config(
                cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                api_key=os.getenv("CLOUDINARY_API_KEY"),
                api_secret=os.getenv("CLOUDINARY_API_SECRET"),
                secure=True
            )
        elif self.mode == "dropbox":
            self.dbx = dropbox.Dropbox(os.getenv("DROPBOX_TOKEN"))

    def upload(self, file, filename):
        if self.mode == "local":
            filepath = os.path.join("media", filename)  # <-- Chemin correct
            # Enregistre en local
            with open(f"media/{filename}", "wb") as f:
                f.write(file.getvalue())
            return f"/media/{filename}"

        elif self.mode == "cloudinary":
            # Upload vers Cloudinary
            result = cloudinary.uploader.upload(file, public_id=filename)
            return result["secure_url"]

        elif self.mode == "dropbox":
            # Upload vers Dropbox
            path = f"/{filename}"
            self.dbx.files_upload(file.getvalue(), path)
            return self.dbx.sharing_create_shared_link(path).url