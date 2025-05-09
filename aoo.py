import streamlit as st
import json
from Scheduler import scheduler
import os
from dotenv import load_dotenv
from insta_session import reload_accounts
from crypto_utils import encrypt_data, decrypt_data
import requests



st.set_page_config(page_title="Planificateur", layout="centered", page_icon="📲")

st.title("📲 Planificateur de VAZAHA CONSULTING")
st.write("Bienvenue ! Choisissez une action dans le menu à gauche.")


def get_public_ip():
    services = [
        "https://api.ipify.org?format=json",
        "https://ipapi.co/json/",
        "https://ipv4.jsonip.com/"
    ]

    for url in services:
        try:
            response = requests.get(url, timeout=15)
            data = response.json()
            return f"{data['ip']} | {data.get('country', 'Unknown')} ✅"
        except:
            continue

    return "Erreur de détection IP ❌"


# Affichez l'IP dans la sidebar
st.sidebar.write("🌐 IP Actuelle")
current_ip = get_public_ip()
if current_ip.startswith("Impossible"):
    st.sidebar.error(current_ip + " (Vérifiez la connexion/VPN)")
else:
    st.sidebar.success(f"`{current_ip}` ✅")

def validate_accounts_file():
    if os.path.exists("accounts.json"):
        try:
            with open("accounts.json", "r") as f:
                accounts = json.load(f)

            # Vérification de l'intégrité des données
            for acc in accounts:
                if "username" not in acc or "password" not in acc:
                    st.error("Fichier accounts.json corrompu. Veuillez le vérifier.")
                    st.stop()

        except json.JSONDecodeError:
            st.error("Fichier accounts.json invalide. Recréez vos comptes.")
            os.remove("accounts.json")


validate_accounts_file()  # Appel au démarrage

# Ajouter un compte
with st.sidebar.form("add_account"):
    st.subheader("Ajouter un compte")
    new_username = st.text_input("Nom d'utilisateur Instagram")
    new_password = st.text_input("Mot de passe", type="password")
    proxy = st.text_input("Proxy (optionnel)", placeholder="IP:port:user:pass")

    if st.form_submit_button("➕ Ajouter"):
        if not new_username or not new_password:
            st.error("❌ Le nom d'utilisateur et le mot de passe sont obligatoires")
            st.stop()

        try:
            # Chargement des comptes existants
            if os.path.exists("accounts.json"):
                with open("accounts.json", "r") as f:
                    existing_accounts = json.load(f)
                    existing_users = [acc["username"] for acc in existing_accounts]
            else:
                existing_accounts = []
                existing_users = []

            if new_username in existing_users:
                st.error("⚠️ Ce compte existe déjà")
                st.stop()

            # Création du nouvel account
            encrypted_password = encrypt_data(new_password)

            new_account = {
                "username": new_username,
                "password": encrypted_password,
                "proxy": proxy
            }

            # Mise à jour du fichier
            updated_accounts = existing_accounts + [new_account] if os.path.exists("accounts.json") else [new_account]

            #sauvegarde:

            with open("accounts.json", "w") as f:
                json.dump(updated_accounts, f, indent=4)

            reload_accounts()
            st.success("Compte ajouté ✅")
            st.rerun()

        except Exception as e:
            st.error(f"Erreur critique : {str(e)}")
            st.stop()

# Supprimer un compte
with st.sidebar.form("delete_account"):
    st.subheader("Supprimer un compte")
    accounts = json.load(open("accounts.json"))
    account_to_delete = st.selectbox("Choisir un compte", [acc["username"] for acc in accounts])
    if st.form_submit_button("🗑️ Supprimer"):
        try:
            # Suppression complète de toutes les données du compte
            updated_accounts = [
                acc for acc in accounts
                if acc["username"] != account_to_delete
            ]

            # Suppression du fichier de session associé
            session_file = os.path.join("sessions", f"{account_to_delete}.json")
            if os.path.exists(session_file):
                os.remove(session_file)

            with open("accounts.json", "w") as f:
                json.dump(updated_accounts, f, indent=4)

            st.success("Compte et données associées supprimés ✅")
            st.rerun()

        except Exception as e:
            st.error(f"Erreur lors de la suppression : {str(e)}")

# 📦 Section "Configuration du Stockage"
st.sidebar.header("☁️ Configuration du Stockage")
storage_mode = st.sidebar.radio(
    "Choisissez un mode de stockage",
    ["Local", "Cloudinary", "Dropbox"],
    index=0  # Par défaut : Local
)

if storage_mode != "Local":
    with st.sidebar.expander("🔑 Configurer les accès cloud"):
        if storage_mode == "Cloudinary":
            cloud_name = st.text_input("Cloud Name", value=os.getenv("CLOUDINARY_CLOUD_NAME", ""))
            api_key = st.text_input("API Key", value=os.getenv("CLOUDINARY_API_KEY", ""))
            api_secret = st.text_input("API Secret", value=os.getenv("CLOUDINARY_API_SECRET", ""))

            if st.button("Enregistrer Cloudinary"):
                os.environ["CLOUDINARY_CLOUD_NAME"] = cloud_name
                os.environ["CLOUDINARY_API_KEY"] = api_key
                os.environ["CLOUDINARY_API_SECRET"] = api_secret
                st.success("Configuration Cloudinary sauvegardée ✅")

        elif storage_mode == "Dropbox":
            dropbox_token = st.text_input("Token Dropbox", type="password")

            if st.button("Enregistrer Dropbox"):
                os.environ["DROPBOX_TOKEN"] = dropbox_token
                st.success("Token Dropbox sauvegardé ✅")


def clear_instagram_cache():
    """Vide le cache Instagram pour éviter les conflits de sessions"""
    cache_dir = os.path.join(os.path.expanduser("~"), ".config", "instagrapi")
    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, file))
        st.success("Cache Instagram nettoyé ✅")
    else:
        st.warning("Aucun cache Instagram trouvé")

# Ajoutez dans la sidebar :
if st.sidebar.button("🧹 Nettoyer le cache Instagram"):
    clear_instagram_cache()

#tester un proxy manuellement
with st.sidebar.expander("🧪 Tester un proxy manuellement"):
    proxy_to_test = st.text_input("Proxy (format ip:port)")
    if st.button("Tester ce proxy"):
        from proxy_manager import test_proxy
        if test_proxy(proxy_to_test):
            st.success("✅ Proxy fonctionnel")
        else:
            st.error("❌ Proxy invalide")