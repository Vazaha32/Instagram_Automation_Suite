import streamlit as st
import sqlite3

st.title("📂 Mes publications planifiées")

# Connexion à la base de données
conn = sqlite3.connect("scheduled_posts.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM posts")
posts = cursor.fetchall()
conn.close()

for post in posts:
    post_id = post[0]
    account = post[1]
    media_type = post[2]
    media_url = post[3]
    caption = post[4]
    publish_date = post[5]

    st.markdown("---")
    st.subheader(f"📸 Post #{post_id} pour @{account}")
    st.write("📅 Date et Heure :", publish_date)
    st.write("🖊️ Caption :", caption)

    if media_type == "image":
        st.image(media_url, width=300)
    elif media_type == "video":
        st.video(media_url)

    if st.button(f"❌ Supprimer cette publication", key=f"delete_{post_id}"):
        conn = sqlite3.connect("scheduled_posts.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        st.success("Publication supprimée ✅")
        st.rerun()  # Actualise la page