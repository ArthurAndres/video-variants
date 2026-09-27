"""Détecte les coupes d'une vidéo (pics de différence inter-images) et les compare aux temps du morceau.
python3 tools/cuts.py video.mp4 [décalage_audio_s]"""
import sys, json, subprocess, numpy as np
V = sys.argv[1]; off = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
W, H = 160, 90
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", V, "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean((1, 2))          # différence moyenne entre images i et i+1
# coupe = pic nettement au-dessus du voisinage (médiane sur ±7 images)
med = np.array([np.median(d[max(0, i - 7): i + 8]) for i in range(len(d))])
cut = [i + 1 for i in range(len(d)) if d[i] > 6 and d[i] > 3.5 * med[i] + 2 and d[i] == d[max(0, i - 2): i + 3].max()]
t_cut = np.array(cut) / 30.0
A = json.load(open("analysis/analysis.json")); bt = np.array(A["temps_s"]) - off
half = np.sort(np.concatenate([bt, (bt[:-1] + bt[1:]) / 2]))
rows = []
for t in t_cut:
    j = np.argmin(abs(bt - t)); k = np.argmin(abs(half - t))
    rows.append((round(float(t), 3), round(float(t - bt[j]), 3), round(float(t - half[k]), 3)))
e = np.array([r[1] for r in rows]); eh = np.array([r[2] for r in rows])
print(f"{len(rows)} coupes détectées ; durée moyenne de plan {len(fr)/30/ (len(rows)+1):.2f} s")
print(f"écart au temps le plus proche : médiane {np.median(abs(e))*1000:.0f} ms, |écart|<=1 image : {np.mean(abs(e)<=1/30)*100:.0f} %")
print(f"écart au temps OU demi-temps : médiane {np.median(abs(eh))*1000:.0f} ms, <=1 image : {np.mean(abs(eh)<=1/30)*100:.0f} %, moyenne signée {eh.mean()*1000:+.0f} ms")
# statisme : différence moyenne par fenêtre de 1,5 s
win = 45; stat = [(round(i / 30, 1), round(float(d[i:i + win].mean()), 2)) for i in range(0, len(d) - win, 15)]
low = [s for s in stat if s[1] < 0.6]
print("fenêtres de 1,5 s quasi statiques (diff moy < 0,6) :", low)
json.dump({"coupes": rows, "statisme": stat}, open("out/review/cuts_test.json", "w"))
for r in rows: print(r)
