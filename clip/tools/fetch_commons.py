"""Télécharge des fichiers Commons (largeur standard ou 0 = original) : python3 tools/fetch_commons.py largeur prefixe:"File name" ..."""
import sys, time, hashlib, urllib.request, urllib.parse
UA = {"User-Agent": "clip-research/0.1 (personal art project; python-urllib)"}
w = sys.argv[1]
for arg in sys.argv[2:]:
    pre, name = arg.split(":", 1)
    # largeur 0 = original ; sinon vignette à une taille STANDARD de Wikimedia (960, 1280, 1920, 3840) : les autres tailles et les gros originaux sont bridés (429)
    fn = name.replace(" ", "_"); h = hashlib.md5(fn.encode()).hexdigest(); q = urllib.parse.quote(fn)
    base = f"https://upload.wikimedia.org/wikipedia/commons/"
    u = base + f"{h[0]}/{h[:2]}/{q}" if w == "0" else base + f"thumb/{h[0]}/{h[:2]}/{q}/{w}px-{q}"
    for k in range(5):
        try:
            data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read(); break
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(5 * 2 ** k)
    else: raise SystemExit(f"échec après 5 essais : {name}")
    ext = name.rsplit(".", 1)[-1].lower().replace("jpeg", "jpg")
    open(f"{pre}.{ext}", "wb").write(data); print(pre, len(data) // 1024, "Ko"); time.sleep(1.5)
