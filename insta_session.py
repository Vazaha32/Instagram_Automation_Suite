# insta_session.py

import json
import os
import streamlit as st
from instagrapi import Client
from time import sleep

from instagrapi.exceptions import ClientNotFoundError, ClientLoginRequired, LoginRequired

from crypto_utils import encrypt_data, decrypt_data

clients = {}
SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


def load_active_sessions():
    """Charge les sessions valides depuis le dossier sessions/"""
    if "accounts" not in st.session_state:
        st.session_state.accounts = []
        session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]

        for file in session_files:
            username = file.replace(".json", "")
            try:
                client = get_client(username)  # Tente de charger la session
                st.session_state.accounts.append({
                    "username": username,
                    "client": client
                })
                print(f"[🔄] Session chargée pour {username}")
            except Exception as e:
                print(f"[⚠️] Session invalide pour {username} : {str(e)}")

def get_account(username):
    """Récupère un compte spécifique depuis accounts.json"""
    accounts = get_accounts()
    for acc in accounts:
        if acc["username"] == username:
            return acc
    raise ClientNotFoundError(f"Compte {username} non trouvé dans accounts.json")

def get_accounts():
    with open("accounts.json", "r") as f:
        return json.load(f)


def get_password(username):
    accounts = get_accounts()
    for account in accounts:
        if account["username"] == username:
            return decrypt_data(acc["password"])  # Déchiffrement
    return None


from instagrapi import Client
from instagrapi.exceptions import BadPassword, ChallengeRequired
import time
import random


def get_client(username):
    try:
        # Configuration avec délais aléatoires
        cl = Client()
        cl.debug = True  # Active les logs détaillés
        cl.allow_retries = False  # Désactive les tentatives automatiques
        cl.delay_range = [5, 10]  # Augmentez les délais entre actions
        cl.request_timeout = 30  # Augmentez le timeout
        cl.proxies = {}  # Force la réinitialisation des proxies
        cl.non_public_requests = True  # Limite les requêtes suspectes
        cl.auto_refresh_delay = 3600  # Rafraîchissement session toutes les heures

        # Force la génération du CSRF token
        cl.get_timeline_feed()  # Test immédiat
        csrf_token = cl.last_response.cookies.get("csrftoken")
        cl.base_headers["X-CSRFToken"] = csrf_token  # Mise à jour dynamique

        # Configuration des headers (méthode validée pour instagrapi 2.1.3+)
        # Nouvelle configuration mobile réaliste
        # Headers
        # Configuration Device/Headers cohérente
        android_id = f"android-{random.randint(10000000, 99999999)}"
        user_agent = "Instagram 287.0.0.0.000 Android (33/13.0.0; 480dpi; 1080x1920; Google; Pixel 8 Pro; raven; raven; en_US)"

        cl.base_headers.update({
            "X-IG-App-ID": "238260118697867",
            "X-IG-Android-ID": android_id,
            "User-Agent": user_agent
        })


        # Désactive les fonctionnalités problématiques
        #cl.set_contact_signup(False)
        #cl.set_allow_contacts_sync(False)



        # Device
        cl.set_device({
            "app_version": "287.0.0.0.000",
            "android_version": 33,
            "android_release": "13.0.0",
            "dpi": "480dpi",
            "resolution": "1080x1920",
            "manufacturer": "Google",
            "model": "Pixel 8 Pro",
            "device_type": "phone"
        })

        # Gestion des proxies
        account = get_account(username)
        if account.get("proxy"):
            cl.set_proxy(account["proxy"])

        # Tentative de connexion
        session_file = os.path.join(SESSIONS_DIR, f"{username}.json")

        if os.path.exists(session_file):
            cl.load_settings(session_file)
            try:
                cl.get_user_info(cl.user_id)  # Test réel de validité
                cl.get_timeline_feed()  # Test silencieux
                return cl
            except Exception:
                os.remove(session_file)  # Session invalide

        # Nouvelle connexion avec gestion d'erreurs
        try:
            password = decrypt_data(account["password"])
            sleep(random.uniform(3.5, 5.5))  # Délai non entier pour éviter la détection
            cl.debug = True
            cl.login(username, password)
            cl.dump_settings(session_file)
            return cl

        except ChallengeRequired as e:
            # Handler interactif
            print(f"Code de sécurité requis pour {username}")
            print(f"URL du challenge : {e.challenge_url}")
            code = st.text_input(f"Entrez le code 2FA/Mail pour {username}:")
            cl.challenge_resolve(e.challenge, code)
            cl.dump_settings(session_file)
            return cl

        except Exception as e:
            print(f"[ERREUR] {username} : {str(e)}")
            raise

        except ChallengeRequired as e:

            # Méthode automatique pour résoudre le challenge SMS

            challenge_code = cl.challenge_code_handler(username, "sms")  # Requiert un handler personnalisé

            cl.challenge_resolve(e.challenge, challenge_code)

        except LoginRequired:
            # Force un FULL relogin
            cl.login(username, password, relogin=True)
            cl.dump_settings(session_file)

        except Exception as e:

            if "login_required" in str(e):
                # Force une nouvelle authentification

                cl.relogin()

        except BadPassword as e:
            if "blacklist" in str(e):
                raise Exception("IP bannie - Changez de réseau ou utilisez un proxy")
            raise

    except Exception as e:
        print(f"[ERREUR GRAVE] {username}: {str(e)}")
        raise


# ✅ INITIALISATION à faire UNE seule fois
if "accounts" not in st.session_state:
    st.session_state.accounts = []
    accounts_data = get_accounts()
    for acc in accounts_data:
        username = acc["username"]
        try:
            client = get_client(username)
            # ✅ Ajoute uniquement les comptes connectés avec succès
            st.session_state.accounts.append({
                "username": username,
                "client": client
            })
            print(f"[OK] {username} connecté.")
        except Exception as e:
            print(f"[Erreur] Impossible de connecter {username}: {e}")
            # ❌ Ne stocke pas le compte en cas d'échec


def reload_accounts():
    """Recharge les comptes depuis accounts.json et met à jour les sessions"""
    accounts_data = get_accounts()
    updated_accounts = []

    for acc in accounts_data:
        username = acc["username"]
        try:
            # Si le client existe déjà, on le conserve
            existing_acc = next((a for a in st.session_state.accounts if a["username"] == username), None)
            if existing_acc:
                updated_accounts.append(existing_acc)
            else:
                # Nouveau compte : connexion + sauvegarde de session
                client = get_client(username)
                updated_accounts.append({"username": username, "client": client})

        except Exception as e:
            print(f"[⚠️] Erreur pour {username} : {str(e)}")

    st.session_state.accounts = updated_accounts
