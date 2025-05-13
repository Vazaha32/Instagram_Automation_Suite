import requests
from bs4 import BeautifulSoup
import concurrent.futures


# Scraper les proxys depuis sslproxies.org
def scrape_proxies():
    url = "https://www.sslproxies.org/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    proxies = []
    table = soup.find("table", {"class": "table table-striped table-bordered"})
    if table:
        rows = table.find_all("tr")[1:]  # Ignorer l'en-tête
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                ip = cols[0].text
                port = cols[1].text
                proxies.append(f"{ip}:{port}")
    return proxies


# Tester un proxy
def test_proxy(proxy):
    try:
        test_url = "http://httpbin.org/ip"
        response = requests.get(
            test_url,
            proxies={"http": f"http://{proxy}", "https": f"https://{proxy}"},
            timeout=5  # Délai maximal
        )
        if response.status_code == 200:
            print(f"[OK] Proxy fonctionnel : {proxy}")
            return proxy
    except Exception as e:
        print(f"[FAIL] Proxy défaillant : {proxy} ({str(e)})")
        return None


# Exécution principale
if __name__ == "__main__":
    proxies = scrape_proxies()
    print(f"{len(proxies)} proxys trouvés. Début des tests...")

    working_proxies = []
    # Utiliser le multithread pour accélérer les tests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(test_proxy, proxies)
        for result in results:
            if result:
                working_proxies.append(result)

    print("\n--- Proxys fonctionnels ---")
    for proxy in working_proxies:
        print(proxy)