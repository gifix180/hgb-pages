"""Relevé PMU pour la page privée « Montes et partants » (23/10/2026).

Lit le programme PMU du jour (réunions en France) et les partants de chaque course, ne garde que les champs utiles
à la page, puis chiffre le tout avec le mot de passe (secret HGB_MOT_DE_PASSE) dans pmu.enc. Données publiques du PMU ;
aucune donnée privée dans ce dépôt (la page index.html est chiffrée par le dépôt privé du projet).

    HGB_MOT_DE_PASSE=… python releve.py [AAAA-MM-JJ]
"""
import base64
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

BASE = "https://online.turfinfo.api.pmu.fr/rest/client/1/programme/"
TOURS = 600_000
SEL = b"hgb-pages-sel-v1"          # même sel que la page (la clé gardée dans le navigateur sert aux deux)
CHAMPS_P = ["numPmu", "nom", "driver", "entraineur", "statut", "gainsParticipant", "handicapDistance", "handicapValeur",
            "handicapPoids", "poidsConditionMonte", "placeCorde", "indicateurInedit", "tauxReclamation", "proprietaire",
            "musique", "dernierRapportDirect"]
CHAMPS_C = ["numOrdre", "heureDepart", "libelle", "conditions", "discipline", "distance", "categorieParticularite",
            "numCourseDedoublee"]


def lire(url):
    for essai in range(3):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "hgb-pages/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # réseau, 5xx : on réessaie
            err = e
            time.sleep(3 * (essai + 1))
    print("échec", url, err)
    return None


def main():
    jour = sys.argv[1] if len(sys.argv) > 1 else datetime.now(ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")
    d = jour[8:10] + jour[5:7] + jour[0:4]
    prog = lire(BASE + d)
    if not prog or "programme" not in prog:
        sys.exit("programme PMU illisible")
    reus = [r for r in prog["programme"]["reunions"] if (r.get("pays") or {}).get("code") == "FRA"]
    data = {BASE + d: {"programme": {"reunions": [
        {"numOfficiel": r["numOfficiel"], "pays": {"code": "FRA"}, "hippodrome": {"libelleCourt": (r.get("hippodrome") or {}).get("libelleCourt")},
         "courses": [{k: c.get(k) for k in CHAMPS_C} for c in r.get("courses", [])]} for r in reus]}}}
    n = 0
    for r in reus:
        for c in r.get("courses", []):
            u = f"{BASE}{d}/R{r['numOfficiel']}/C{c['numOrdre']}/participants"
            j = lire(u)
            data[u] = {"participants": [{k: p.get(k) for k in CHAMPS_P if k in p} for p in j.get("participants", [])]} if j else None
            n += 1
    clair = json.dumps({"date": jour, "at": int(time.time() * 1000), "data": data}, ensure_ascii=False, separators=(",", ":"))
    mdp = os.environ["HGB_MOT_DE_PASSE"]
    cle = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SEL, iterations=TOURS).derive(mdp.encode())
    iv = os.urandom(12)
    ct = AESGCM(cle).encrypt(iv, clair.encode("utf-8"), None)
    with open("pmu.enc", "w") as f:
        json.dump({"iv": base64.b64encode(iv).decode(), "ct": base64.b64encode(ct).decode()}, f)
    print(f"{jour} : {len(reus)} réunion(s), {n} course(s), {len(clair) // 1024} Ko")


if __name__ == "__main__":
    main()
