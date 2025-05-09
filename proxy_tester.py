import streamlit as st
import requests

def is_proxy_alive(proxy):
    try:
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}",
        }
        r = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=5)
        return r.json()["ip"]
    except:
        return None

st.title("🧪 Testeur de Proxies HTTPS")

proxy_list = st.text_area("Colle ici ta liste de proxies (format IP:PORT)", height=200)

if st.button("Tester les proxies"):
    proxies = [p.strip() for p in proxy_list.splitlines() if p.strip()]
    good = []

    with st.spinner("Test en cours..."):
        for proxy in proxies:
            ip = is_proxy_alive(proxy)
            if ip:
                good.append(f"{proxy} ✅ ({ip})")
            else:
                st.error(f"{proxy} ❌")

    if good:
        st.success(f"{len(good)} proxies fonctionnels trouvés:")
        st.code("\n".join(good))
    else:
        st.warning("Aucun proxy fonctionnel trouvé.")
