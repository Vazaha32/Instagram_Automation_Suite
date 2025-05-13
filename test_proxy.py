import requests

# Configuration du proxy Bright Data
proxy_host = "brd.superproxy.io"
proxy_port = "33335"
proxy_username = "brd-customer-hl_d992665e-zone-residential_proxy1"
proxy_password = "z3b6sv4kh6ty"

# Format attendu : http://user:pass@host:port
proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}"

# Test de connexion
test_url = "http://lumtest.com/myip.json"  # Service qui retourne votre IP apparente

try:
    response = requests.get(
        test_url,
        proxies={
            "http": proxy_url,
            "https": proxy_url
        },
        timeout=10
    )

    if response.status_code == 200:
        ip_data = response.json()
        print(f"✅ Proxy fonctionnel !\nIP utilisée : {ip_data['ip']}\nPays : {ip_data['country']}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}")

except Exception as e:
    print(f"❌ Erreur de connexion : {str(e)}")