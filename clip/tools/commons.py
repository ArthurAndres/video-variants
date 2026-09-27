"""Recherche d'images sur Wikimedia Commons : python3 tools/commons.py "requête" [n]"""
import sys, json, urllib.request, urllib.parse, re
UA = {"User-Agent": "clip-research/0.1 (personal art project; python-urllib)"}
import time
def api(**p):
    p.update(format="json", action="query")
    u = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(p)
    for k in range(5):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30))
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            w = int(e.headers.get("Retry-After", 0) or 0) or 5 * 2 ** k; print(f"429, attente {w} s", file=sys.stderr); time.sleep(w)
    raise SystemExit("Commons : trop de requêtes")
q = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
d = api(generator="search", gsrsearch=f"filetype:bitmap {q}", gsrnamespace=6, gsrlimit=n,
        prop="imageinfo", iiprop="url|size|extmetadata", iiextmetadatafilter="LicenseShortName|Artist")
for p in sorted(d.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0)):
    ii = p["imageinfo"][0]; m = ii.get("extmetadata", {})
    lic = m.get("LicenseShortName", {}).get("value", "?"); art = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "?"))[:40]
    print(f'{ii["width"]}x{ii["height"]} | {lic} | {art} | {p["title"]}\n    {ii["url"]}')
