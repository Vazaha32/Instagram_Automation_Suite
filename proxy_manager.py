# proxy_manager.py
import requests
from bs4 import BeautifulSoup

def get_sslproxies(limit=20):
    url = "https://www.sslproxies.org/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table", attrs={"id": "proxylisttable"})

    if table is None:
        raise Exception("❌ Impossible de trouver la table des proxys sur sslproxies.org")

    proxies = []
    for row in table.tbody.find_all("tr")[:limit]:
        cols = row.find_all("td")
        ip = cols[0].text
        port = cols[1].text
        proxies.append(f"{ip}:{port}")
    return proxies

def test_proxy(proxy):
    try:
        response = requests.get("https://api.ipify.org?format=json",
                                proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                                timeout=5)
        return response.status_code == 200
    except:
        return False

def get_working_proxies(limit=10):
    candidates = get_sslproxies(limit=50)
    working = []
    for proxy in candidates:
        if test_proxy(proxy):
            print(f"[✅] {proxy}")
            working.append(proxy)
            if len(working) >= limit:
                break
        else:
            print(f"[❌] {proxy}")
    return working
