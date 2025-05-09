import os
import sqlite3
import tempfile
import random
import time
from datetime import datetime
import requests
from insta_session import get_client
from apscheduler.schedulers.background import BackgroundScheduler


def check_posts():
    print("[📅] Vérification des posts...")

    try:
        # Connexion à la base de données
        conn = sqlite3.connect("scheduled_posts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM posts")
        posts = cursor.fetchall()
    finally:
        conn.close()

    for post in posts:
        post_id, account, media_type, media_url, caption, publish_date_str = post
        tmp_path = None  # Déclaration pour le bloc finally

        try:
            # Vérification de la date
            post_time = datetime.strptime(publish_date_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < post_time:
                continue

            # Téléchargement du média
            with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".mp4" if media_type == "reel" else ".jpg"
            ) as tmp_file:
                response = requests.get(media_url)
                tmp_file.write(response.content)
                tmp_path = tmp_file.name

            # Publication
            client = get_client(account)
            if media_type == "image":
                client.photo_upload(tmp_path, caption)
            elif media_type == "reel":
                client.video_upload(tmp_path, caption)

            # Suppression de la base de données
            with sqlite3.connect("scheduled_posts.db") as conn:
                conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))

            print(f"✅ Post publié pour {account}")

        except Exception as e:
            print(f"❌ Erreur pour {account}: {str(e)}")

        finally:
            # Nettoyage du fichier temporaire
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    # Délai aléatoire après le traitement complet
    time.sleep(random.randint(1, 30))


# Configuration du scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    check_posts,
    'interval',
    minutes=5,
    max_instances=1  # Empêche les exécutions parallèles
)
scheduler.start()