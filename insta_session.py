# insta_session.py
import json
import os
import re
import logging
import random
import time
import requests
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup

import streamlit as st
from instagrapi import Client
from instagrapi.exceptions import (
    ClientError,
    ClientLoginRequired,
    ChallengeRequired,
    LoginRequired,
    BadPassword
)

from crypto_utils import decrypt_data

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


# ----------------------------------------------------------
# Fonction de scraping de proxies
# ----------------------------------------------------------
def scrape_sslproxies(max_proxies=20):
    """Scrappe les proxies HTTPS gratuits depuis sslproxies.org"""
    try:
        url = 'https://www.sslproxies.org/'
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        proxies = []
        table = soup.find('table', {'id': 'proxylisttable'})

        if table:
            for row in table.tbody.find_all('tr')[:max_proxies]:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    ip = cells[0].text.strip()
                    port = cells[1].text.strip()
                    proxies.append(f"{ip}:{port}")

        logger.info(f"Scraped {len(proxies)} proxies from sslproxies.org")
        return proxies

    except Exception as e:
        logger.error(f"Erreur de scraping: {str(e)}")
        return []


# ----------------------------------------------------------
# Configuration aléatoire du device
# ----------------------------------------------------------
def get_random_device():
    android_versions = [
        (29, "10.0.0"),
        (30, "11.0.0"),
        (31, "12.0.0"),
        (33, "13.0.0")
    ]
    version, release = random.choice(android_versions)

    return {
        "app_version": "287.0.0.0.000",
        "android_version": version,
        "android_release": release,
        "dpi": "480dpi",
        "resolution": "1080x1920",
        "manufacturer": random.choice(["Google", "Samsung", "Xiaomi"]),
        "model": random.choice(["Pixel 7 Pro", "SM-G998B", "22021211RG"]),
        "device_type": "phone",
        "user_agent": (
            f"Instagram 287.0.0.0.000 Android ({version}/{release}; "
            f"480dpi; 1080x1920; {random.choice(['Google', 'Samsung'])}; "
            f"{random.choice(['Pixel 7 Pro', 'Galaxy S22 Ultra'])}; "
            f"{random.choice(['raven', 'oriole'])}; en_US)"
        )
    }


# ----------------------------------------------------------
# Gestion des proxies
# ----------------------------------------------------------
def format_proxy(proxy_str):
    """Formate le proxy en ajoutant https:// si nécessaire"""
    if not proxy_str:
        return None

    # Vérifie si le proxy a déjà un protocole
    if not re.match(r'^https?://', proxy_str):
        proxy_str = f"https://{proxy_str}"

    # Validation basique de l'adresse IP
    if not re.match(r'^https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$', proxy_str):
        raise ValueError("Format de proxy invalide. Utilisez ip:port")

    return proxy_str


# ----------------------------------------------------------
# Gestion des comptes
# ----------------------------------------------------------
def get_accounts():
    """Charge les comptes depuis accounts.json"""
    try:
        with open("accounts.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_client(username, max_retries=2):
    """Crée ou récupère un client Instagram avec gestion améliorée des proxies"""
    try:
        account = next((acc for acc in get_accounts() if acc["username"] == username), None)
        if not account:
            raise ClientError(f"Compte {username} introuvable")

        cl = Client()
        cl.delay_range = [2, 5]
        cl.request_timeout = 30

        # Configuration aléatoire
        device_config = get_random_device()
        cl.set_device(device_config)
        cl.set_user_agent(device_config["user_agent"])

        # Gestion du proxy (optionnel)
        proxy = None
        if account.get("proxy"):
            try:
                proxy = format_proxy(account["proxy"])
                cl.set_proxy(proxy)
                logger.info(f"Utilisation du proxy: {proxy}")
            except Exception as e:
                logger.warning(f"Proxy invalide: {str(e)}")

        session_file = os.path.join(SESSIONS_DIR, f"{username}.json")
        password = decrypt_data(account["password"])

        # Tentative de connexion avec reprise
        for attempt in range(1, max_retries + 1):
            try:
                if os.path.exists(session_file) and attempt == 1:
                    cl.load_settings(session_file)
                    cl.get_timeline_feed()  # Test de validité
                    return cl

                cl.login(username, password)
                cl.dump_settings(session_file)
                return cl

            except (ChallengeRequired, LoginRequired) as e:
                logger.warning(f"Challenge requis pour {username} (tentative {attempt}/{max_retries})")
                handle_challenge(cl, username, e)

            except BadPassword as e:
                if "blacklist" in str(e) and proxy:
                    logger.error("IP bannie - Changez de proxy")
                    raise

                if attempt == max_retries:
                    raise

            sleep(5 * attempt)  # Backoff exponentiel

    except Exception as e:
        logger.error(f"Échec de connexion pour {username}: {str(e)}")
        raise


# ----------------------------------------------------------
# Gestion des challenges (2FA/SMS)
# ----------------------------------------------------------
def handle_challenge(client, username, challenge_exception):
    """Gère les demandes de vérification via l'interface Streamlit"""
    with st.expander(f"🔒 VÉRIFICATION REQUISE POUR {username.upper()}", expanded=True):
        st.write(f"**Méthode de vérification:** {challenge_exception.challenge_type}")
        st.write(f"**URL du challenge:** {challenge_exception.challenge_url}")

        code = st.text_input(f"Entrez le code reçu pour {username}:")
        if st.button("Valider le code"):
            try:
                client.challenge_resolve(challenge_exception.challenge, code)
                client.dump_settings(os.path.join(SESSIONS_DIR, f"{username}.json"))
                st.success("Vérification réussie !")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Échec de vérification: {str(e)}")

    st.stop()


# ----------------------------------------------------------
# Fonctions principales
# ----------------------------------------------------------
def reload_accounts():
    """Recharge tous les comptes avec gestion des erreurs"""
    try:
        cleanup_sessions()
        accounts = get_accounts()
        valid_accounts = []

        for acc in accounts:
            username = acc["username"]
            try:
                client = get_client(username)
                valid_accounts.append({
                    "username": username,
                    "client": client,
                    "last_active": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Échec du chargement pour {username}: {str(e)}")

        st.session_state.accounts = valid_accounts

    except Exception as e:
        logger.error(f"Erreur critique: {str(e)}")
        raise


def cleanup_sessions():
    """Nettoie les sessions des comptes supprimés"""
    existing_users = [acc["username"] for acc in get_accounts()]
    for fname in os.listdir(SESSIONS_DIR):
        username = os.path.splitext(fname)[0]
        if username not in existing_users:
            os.remove(os.path.join(SESSIONS_DIR, fname))
            logger.info(f"Session nettoyée: {username}")


# Initialisation
if "accounts" not in st.session_state:
    reload_accounts()