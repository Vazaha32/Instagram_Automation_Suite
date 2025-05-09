import os
import tempfile
import streamlit as st
from insta_session import get_client
from insta_session import get_client, load_active_sessions

st.title("Modifier le profil Instagram")

load_active_sessions()

# 🔐 Vérifie la connexion des comptes
if "accounts" not in st.session_state or not st.session_state.accounts:
    st.warning("Aucun compte connecté. Connectez-vous d'abord depuis la page principale.")
    st.stop()

# 👤 Liste des comptes
usernames = [acc["username"] for acc in st.session_state.accounts]
selected_username = st.selectbox("Choisissez un compte à modifier", usernames)

# Récupération dynamique du client

client = get_client(selected_username)  # <-- Appel direct à get_client()

if not client:
    st.error("❌ Compte non connecté. Reconnectez-vous.")
    st.stop()
# 📋 Infos du profil
try:
    profile = client.account_info()
except Exception as e:
    st.error(f"Erreur : {e}")
    st.stop()

# ✍️ Formulaire de modification
new_name = st.text_input("Nom complet", value=profile.full_name)
new_bio = st.text_area("Bio", value=profile.biography)
new_pfp = st.file_uploader("Photo de profil", type=["jpg", "jpeg", "png"])

if st.button("Appliquer les modifications"):
    try:
        # Mise à jour du nom et bio
        client.account_edit(full_name=new_name, biography=new_bio)

        # Mise à jour de la photo
        if new_pfp:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                tmp_file.write(new_pfp.read())
                tmp_path = tmp_file.name
            client.account_change_picture(tmp_path)
            os.remove(tmp_path)  # ✅ Nettoyage

        st.success("✅ Modifications enregistrées !")
    except Exception as e:
        st.error(f"❌ Erreur : {e}")