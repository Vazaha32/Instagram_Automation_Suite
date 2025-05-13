import requests
from bs4 import BeautifulSoup
import concurrent.futures
import streamlit as st


def scrape_proxies():
    """Scrape SSLProxies and return only HTTPS-capable proxies"""
    try:
        url = "https://www.sslproxies.org/"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        proxies = []
        table = soup.find("table", {"class": "table table-striped table-bordered"})

        if table:
            # Each row: [IP, Port, Code, Country, Anonymity, Google, HTTPS, Last Checked]
            for row in table.find_all("tr")[1:100]:  # limit to first 100
                cols = row.find_all("td")
                if len(cols) >= 7:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    https_flag = cols[6].text.strip().lower()
                    if https_flag == 'yes':
                        proxies.append(f"{ip}:{port}")
        return proxies

    except Exception as e:
        st.error(f"Erreur lors du scraping des proxys : {e}")
        return []


def test_proxy(proxy):
    """Test a single proxy by requesting httpbin via HTTPS"""
    try:
        test_url = "https://httpbin.org/ip"
        response = requests.get(
            test_url,
            proxies={"https": f"https://{proxy}"},
            timeout=7
        )
        return response.status_code == 200
    except Exception:
        return False


def get_working_proxies():
    """Fetch and test HTTPS proxies in parallel"""
    proxies = scrape_proxies()
    if not proxies:
        return []

    working = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(test_proxy, p): p for p in proxies}
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            try:
                if future.result():
                    working.append(p)
            except Exception:
                continue
    return working


def show_proxy_interface():
    """Streamlit sidebar UI for proxy selection"""
    with st.sidebar.expander("🔌 PROXYS (Cliquez pour développer)", expanded=True):
        if st.button("🔄 Scraper les proxys", key="scrape_btn"):
            with st.spinner("Recherche de proxys HTTPS valides..."):
                st.session_state.working_proxies = get_working_proxies()
                st.rerun()

        if 'working_proxies' in st.session_state:
            if st.session_state.working_proxies:
                selected = st.selectbox(
                    "Proxys HTTPS disponibles :",
                    st.session_state.working_proxies,
                    key="proxy_selector"
                )
                st.session_state.selected_proxy = selected
                st.success(f"Proxy sélectionné : `{selected}`")
            else:
                st.error("Aucun proxy HTTPS valide trouvé")


def debug_proxy_scraping():
    """Fonction de débogage pour tester le scraping hors Streamlit"""
    print("### Début du débogage ###")

    # Test scraping
    proxies = scrape_proxies()
    print(f"Proxies trouvés ({len(proxies)}):")
    print('\n'.join(proxies[:5]))  # Affiche les 5 premiers

    # Test proxy
    if proxies:
        test_result = test_proxy(proxies[0])
        print(f"Test proxy {proxies[0]} : {'Réussi' if test_result else 'Échec'}")

    print("### Fin du débogage ###")
