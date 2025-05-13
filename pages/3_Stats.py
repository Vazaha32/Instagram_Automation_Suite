# pages/3_Stats.py

import streamlit as st
from insta_session import get_accounts, get_client

st.title("📊 Statistiques Instagram")

accounts = get_accounts()
account_usernames = [acc["username"] for acc in accounts]

selected_username = st.selectbox("Choisissez un compte :", account_usernames)

if st.button("Afficher les stats"):
    with st.spinner("Récupération des stats..."):
        client = get_client(selected_username)
        user_id = client.user_id_from_username(selected_username)
        user_info = client.user_info(user_id)

        st.subheader(f"📈 Statistiques de @{selected_username}")
        st.write(f"👥 Followers : {user_info.follower_count}")
        st.write(f"🫂 Abonnements : {user_info.following_count}")
        st.write(f"📝 Nombre de posts : {user_info.media_count}")
        st.write(f"📍 Biographie : {user_info.biography}")
