import streamlit as st
import json
import os
import requests
from dotenv import load_dotenv
from Scheduler import scheduler
from insta_session import reload_accounts
from crypto_utils import encrypt_data, decrypt_data
from proxy_manager import show_proxy_interface, scrape_proxies, get_working_proxies

# Configuration initiale
st.set_page_config(
    page_title="Planificateur Instagram",
    page_icon="📲",
    layout="centered"
)

# Titre principal
st.title("📲 Planificateur de VAZAHA CONSULTING")
st.write("Bienvenue ! Choisissez une action dans le menu à gauche.")

# Validation du fichier accounts.json
def validate_accounts_file():
    if os.path.exists("accounts.json"):
        try:
            with open("accounts.json", "r") as f:
                accounts = json.load(f)
                if not isinstance(accounts, list):
                    raise ValueError("Format invalide")
                for acc in accounts:
                    if "username" not in acc:
                        raise KeyError("Clé 'username' manquante")
        except Exception as e:
            st.error(f"Fichier accounts.json corrompu : {str(e)}")
            os.rename("accounts.json", "accounts_corrompu.json")
            st.stop()

validate_accounts_file()

# Fonction pour obtenir l'IP publique
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

# Sidebar
with st.sidebar:
    # Section Proxy Manager
    show_proxy_interface()

    # Section Ajout de compte
    with st.form("add_account_form", clear_on_submit=True):
        st.subheader("Ajouter un compte")
        new_username = st.text_input("Nom d'utilisateur Instagram", key="add_user")
        new_password = st.text_input("Mot de passe", type="password", key="add_pass")
        proxy = st.text_input(
            "Proxy (optionnel)",
            value=st.session_state.get('selected_proxy', ''),
            placeholder="Ex: 176.126.85.187:8080",
            key="proxy_input"
        )

        if st.form_submit_button("➕ Ajouter"):
            if not new_username or not new_password:
                st.error("❌ Le nom d'utilisateur et le mot de passe sont obligatoires")
                st.stop()

            try:
                with open("accounts.json", "r") as f:
                    existing_accounts = json.load(f)
                    existing_users = [acc["username"] for acc in existing_accounts]
            except FileNotFoundError:
                existing_accounts = []
                existing_users = []

            if new_username in existing_users:
                st.error("⚠️ Ce compte existe déjà")
                st.stop()

            new_account = {
                "username": new_username,
                "password": encrypt_data(new_password),
                "proxy": proxy
            }

            with open("accounts.json", "w") as f:
                json.dump(existing_accounts + [new_account], f, indent=4)

            reload_accounts()
            st.success("Compte ajouté ✅")
            st.rerun()

    # Section Suppression de compte
    if os.path.exists("accounts.json"):
        with st.form("delete_account_form"):
            st.subheader("Supprimer un compte")
            accounts = json.load(open("accounts.json"))
            account_to_delete = st.selectbox(
                "Choisir un compte",
                [acc["username"] for acc in accounts],
                key="delete_select"
            )
            if st.form_submit_button("🗑️ Supprimer"):
                updated_accounts = [acc for acc in accounts if acc["username"] != account_to_delete]
                session_file = os.path.join("sessions", f"{account_to_delete}.json")
                if os.path.exists(session_file):
                    os.remove(session_file)
                with open("accounts.json", "w") as f:
                    json.dump(updated_accounts, f, indent=4)
                st.success("Compte supprimé ✅")
                st.rerun()

    # Section Configuration du Stockage
    st.header("☁️ Configuration du Stockage")
    storage_mode = st.radio(
        "Choisissez un mode de stockage",
        ["Local", "Cloudinary", "Dropbox"],
        index=0,
        key="storage_radio"
    )


    # Appeler dans aoo.py
    from proxy_manager import debug_proxy_scraping

    debug_proxy_scraping()

    if storage_mode != "Local":
        with st.expander("🔑 Configurer les accès cloud"):
            if storage_mode == "Cloudinary":
                cloud_name = st.text_input("Cloud Name", value=os.getenv("CLOUDINARY_CLOUD_NAME", ""), key="cloud_name")
                api_key = st.text_input("API Key", value=os.getenv("CLOUDINARY_API_KEY", ""), key="api_key")
                api_secret = st.text_input("API Secret", value=os.getenv("CLOUDINARY_API_SECRET", ""), key="api_secret")
                if st.button("Enregistrer Cloudinary", key="save_cloudinary"):
                    os.environ["CLOUDINARY_CLOUD_NAME"] = cloud_name
                    os.environ["CLOUDINARY_API_KEY"] = api_key
                    os.environ["CLOUDINARY_API_SECRET"] = api_secret
                    st.success("Configuration sauvegardée ✅")

            elif storage_mode == "Dropbox":
                dropbox_token = st.text_input("Token Dropbox", type="password", key="dropbox_token")
                if st.button("Enregistrer Dropbox", key="save_dropbox"):
                    os.environ["DROPBOX_TOKEN"] = dropbox_token
                    st.success("Token sauvegardé ✅")

    # Nettoyage du cache
    if st.button("🧹 Nettoyer le cache Instagram", key="clear_cache"):
        cache_dir = os.path.join(os.path.expanduser("~"), ".config", "instagrapi")
        if os.path.exists(cache_dir):
            for file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, file))
            st.success("Cache nettoyé ✅")
        else:
            st.warning("Aucun cache trouvé")

# Contenu principal
current_ip = get_public_ip()
st.sidebar.write("🌐 IP Actuelle")
if current_ip.startswith("Erreur"):
    st.sidebar.error(current_ip)
else:
    st.sidebar.success(f"`{current_ip}` ✅")

