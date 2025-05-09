# pages/4_DMs.py

import streamlit as st
from insta_session import get_accounts, get_client

st.title("✉️ Gestion des DMs Instagram")

accounts = get_accounts()
account_usernames = [acc["username"] for acc in accounts]

selected_username = st.selectbox("Choisissez un compte :", account_usernames)

if st.button("Voir les DMs"):
    with st.spinner("Connexion au compte..."):
        try:
            client = get_client(selected_username)
            threads = client.direct_threads()

            for thread in threads:
                st.subheader(f"🧵 Thread avec {', '.join([user.username for user in thread.users])}")
                for message in thread.messages[:10]:  # afficher les 10 derniers messages
                    sender = message.user_id
                    content = message.text if message.text else "[Media]"
                    st.write(f"📩 {sender} : {content}")

        except Exception as e:
            st.error(f"Erreur : {e}")

st.divider()

st.subheader("Envoyer un DM")
recipient_username = st.text_input("Nom d'utilisateur du destinataire (sans @)")
message_text = st.text_area("Votre message")

if st.button("Envoyer le message"):
    try:
        client = get_client(selected_username)
        user_id = client.user_id_from_username(recipient_username)
        client.direct_send(message_text, [user_id])
        st.success("✅ Message envoyé avec succès !")
    except Exception as e:
        st.error(f"Erreur : {e}")
