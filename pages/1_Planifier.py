# pages/1_Planifier.py

import streamlit as st
from cloudinary_config import upload_image, upload_video
from datetime import datetime
import json
from moviepy.editor import VideoFileClip  # Pour vérifier la durée et la résolution
from insta_session import get_client
import sqlite3
from storage_manager import StorageManager


# Charger les comptes en session
if "accounts" not in st.session_state:
    with open("accounts.json","r") as f:
        st.session_state.accounts = json.load(f)

st.title("📝 Planifier une publication")

ACCOUNTS = [acc["username"] for acc in st.session_state.accounts]
account = st.selectbox("📍 Choisissez le compte :", ACCOUNTS)

# Ajoutez un bouton de rafraîchissement :
if st.button("🔄 Rafraîchir la liste des comptes"):
    with open("accounts.json", "r") as f:
        st.session_state.accounts = json.load(f)
    st.rerun()

media_type = st.radio("Type de publication", ["image", "reel"])
uploaded_file = st.file_uploader(
    "📤 Importer un fichier",
    type = ["jpg","jpeg","png"] if media_type=="image" else ["mp4"]
)
caption = st.text_area("🖊️ Légende (caption)")
publish_date = st.date_input("📅 Date de publication", min_value=datetime.now())
publish_time = st.time_input("🕒 Heure de publication")

if uploaded_file:
    st.write("Aperçu :")
    if media_type=="image":
        st.image(uploaded_file, use_column_width=True)
    else:
        st.video(uploaded_file)

if st.button("✅ Planifier"):
    storage = StorageManager()
    media_url = storage.upload(uploaded_file, uploaded_file.name)
    # 1) Upload sur Cloudinary
    if media_type=="image":
        media_url = upload_image(uploaded_file).replace("\\", "/")  # ✅ Formatage correct
    else:
        media_url = upload_video(uploaded_file).replace("\\", "/")  # ✅ Formatage correct
    st.success("Media uploadé sur Cloudinary ✅")


    # 3) Enregistrer la planification
    post_data = {
        "account": account,
        "media_type": media_type,
        "media_url": media_url,
        "caption": caption,
        "publish_date": publish_date.isoformat(),
        "publish_time": publish_time.strftime("%H:%M:%S")
    }

    #Fonctions utilitaires
    def get_video_duration(video_path):
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration


    def get_video_resolution(video_path):
        clip = VideoFileClip(video_path)
        width, height = clip.size
        clip.close()
        return width, height

    # Connexion à la base de données
    conn = sqlite3.connect("scheduled_posts.db")
    cursor = conn.cursor()
    # Crée la table si elle n'existe pas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            account TEXT,
            media_type TEXT,
            media_url TEXT,
            caption TEXT,
            publish_date TEXT
        )
    ''')
    # Ajoute le post
    cursor.execute('''
        INSERT INTO posts (account, media_type, media_url, caption, publish_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (account, media_type, media_url, caption, f"{publish_date} {publish_time}"))
    conn.commit()
    conn.close()

    st.success("📅 Publication planifiée enregistrée.")
