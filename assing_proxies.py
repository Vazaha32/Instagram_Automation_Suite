# assign_proxies.py
#1.version automatique
import json
from proxy_manager import get_working_proxies

# Charger les comptes
#with open("accounts.json", "r") as f:
 #   accounts = json.load(f)

# Obtenir des proxys valides
#working_proxies = get_working_proxies(limit=len(accounts))

# Assigner un proxy par compte
#for i, account in enumerate(accounts):
#    if i < len(working_proxies):
#        account["proxy"] = working_proxies[i]
#    else:
#        print(f"[⚠️] Pas assez de proxys valides pour {account['username']}")
#        account["proxy"] = ""  # Aucun proxy assigné

# Sauvegarde
#with open("accounts.json", "w") as f:
#    json.dump(accounts, f, indent=4)

#print("[✔] Proxys assignés à accounts.json")

#version par défaut
from proxy_manager import get_sslproxies, test_proxy


def test_all_proxies():
    proxies = get_sslproxies(limit=30)
    print(f"🔍 {len(proxies)} proxies récupérés")

    working = []
    for proxy in proxies:
        if test_proxy(proxy):
            print(f"[✅] {proxy}")
            working.append(proxy)
        else:
            print(f"[❌] {proxy}")

    print(f"\n🟢 Total fonctionnels : {len(working)}")
    return working

if __name__ == "__main__":
    test_all_proxies()


if __name__ == "__main__":
    test_all_proxies()
