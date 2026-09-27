"""Analyse du morceau (section 5.2) -> analysis/analysis.json, analysis/carte.png, analysis/mesures.md"""
import json, sys
import numpy as np, librosa, scipy.signal as sg, scipy.ndimage as nd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else "references/you_know_my_name.mp3"
OUT = "analysis/"
SR, HOP = 22050, 512
y, sr = librosa.load(SRC, sr=SR, mono=True)
dur = len(y) / sr
fps = sr / HOP

# ---------- énergie (RMS relatif, 2 valeurs/s + courbe fine) ----------
rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=HOP)[0]
t_rms = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=HOP)
rms_n = rms / np.percentile(rms, 99)
step = 0.5
e_t = np.arange(0, dur, step)
e_v = np.array([rms_n[(t_rms >= a) & (t_rms < a + step)].mean() for a in e_t])

# ---------- coupure finale : dernier instant où l'énergie passe sous 2 % du médian ----------
lvl = librosa.amplitude_to_db(rms, ref=np.median(rms))
loud = np.where(lvl > -30)[0]
cut_frame = loud[-1]
# affinage à l'échantillon : dernière fenêtre de 5 ms au-dessus du seuil
env = np.abs(y); win = int(0.005 * sr)
blk = env[: len(env) // win * win].reshape(-1, win).max(1)
thr = np.median(blk) * 0.05
cut_t = float(np.where(blk > thr)[0][-1] * win / sr)
# début de chute : dernier bloc de 50 ms à moins de 6 dB du niveau des 10 s précédentes ; silence : premier bloc à -40 dB
b50 = int(0.05 * sr); r50 = np.sqrt(np.mean(y[: len(y) // b50 * b50].reshape(-1, b50) ** 2, 1)) + 1e-9
d50 = 20 * np.log10(r50 / np.median(r50[int((cut_t - 12) / 0.05): int((cut_t - 2) / 0.05)]))
i0 = int((cut_t - 3) / 0.05)
cut_start = float((i0 + np.where(d50[i0:] > -6)[0][-1] + 1) * 0.05)
cut_silence = float((i0 + np.where(d50[i0:] < -40)[0][0]) * 0.05)
tail_db = float(librosa.amplitude_to_db(np.array([np.sqrt(np.mean(y[int((cut_t + 0.2) * sr):] ** 2)) + 1e-9]), ref=np.sqrt(np.mean(y ** 2)))[0])

# ---------- onsets, tempo, temps ----------
oenv = librosa.onset.onset_strength(y=y, sr=sr, hop_length=HOP, aggregate=np.median)
tg = librosa.feature.tempogram(onset_envelope=oenv, sr=sr, hop_length=HOP)
ac = np.mean(tg, axis=1); bpms = librosa.tempo_frequencies(tg.shape[0], sr=sr, hop_length=HOP)
def ac_at(b):  # force de l'autocorrélation au tempo b
    i = np.argmin(np.abs(bpms - b)); return float(ac[i])
# suivi fin (5,8 ms) puis recalage de chaque temps sur le pic d'attaque local, puis lissage robuste
FSR, FH = 44100, 256
yf, _ = librosa.load(SRC, sr=FSR, mono=True)
of = librosa.onset.onset_strength(y=yf, sr=FSR, hop_length=FH, aggregate=np.median, lag=2)
ffr = FSR / FH
_, beats = librosa.beat.beat_track(onset_envelope=of, sr=FSR, hop_length=FH, bpm=137, tightness=800, trim=False)
raw = librosa.frames_to_time(beats, sr=FSR, hop_length=FH); raw = raw[raw < cut_t]
ref = []
for t in raw:
    c = int(round(t * ffr)); w = int(0.035 * ffr); lo, hi = max(1, c - w), min(len(of) - 2, c + w)
    k = lo + int(np.argmax(of[lo:hi + 1])); p0, p1, p2 = of[k - 1], of[k], of[k + 1]
    ref.append((k + np.clip(0.5 * (p0 - p2) / (p0 - 2 * p1 + p2 + 1e-9), -.5, .5)) / ffr)
ref = np.array(ref); n = len(ref); bt = ref.copy()
for _ in range(3):
    new = np.empty(n)
    for i in range(n):
        lo, hi = max(0, i - 4), min(n, i + 5); x = np.arange(lo, hi)
        r = ref[lo:hi] - np.interp(x, np.arange(n), bt); w = np.clip(1 - (r / 0.06) ** 2, 0, 1) ** 2 + 1e-3
        new[i] = np.polyval(np.polyfit(x, ref[lo:hi], 1, w=w), i)
    bt = new
ibi = np.diff(bt); tempo = 60 / ibi.mean()
loc = [(round(float(bt[i]), 1), round(float(60 / np.polyfit(np.arange(16), bt[i:i + 16], 1)[0]), 2)) for i in range(0, n - 16, 8)]
gi = np.arange(n); gp = np.polyfit(gi, bt, 1); gres = bt - np.polyval(gp, gi)

# test demi / double tempo : force des onsets aux temps, aux demi-temps, au hasard ; autocorrélation
def strength_at(times):
    f = np.clip((np.asarray(times) * ffr).astype(int), 3, len(of) - 4)
    return float(np.mean([of[i - 3: i + 4].max() for i in f]))
s_beat, s_half = strength_at(bt), strength_at((bt[:-1] + bt[1:]) / 2)
s_rand = strength_at(np.random.default_rng(0).uniform(bt[0], bt[-1], 2000))
tempo_check = {
    "tempo_retenu_bpm": round(float(tempo), 2),
    "tempo_local_min_max": [min(l[1] for l in loc), max(l[1] for l in loc)],
    "autocorr_tempo": round(ac_at(tempo), 3), "autocorr_demi_tempo": round(ac_at(tempo / 2), 3), "autocorr_double_tempo": round(ac_at(tempo * 2), 3),
    "attaque_moy_sur_temps": round(s_beat, 3), "attaque_moy_sur_demi_temps": round(s_half, 3), "attaque_moy_aleatoire": round(s_rand, 3),
    "grille_fixe_si_on_l_imposait": {"bpm": round(float(60 / gp[0]), 3), "derive_max_s": round(float(abs(gres).max()), 3)},
    "tempo_local_16_temps": loc,
}

# ---------- premiers temps de mesure (4/4) : phase qui maximise basse + attaque ----------
S = np.abs(librosa.stft(y, hop_length=HOP))
freqs = librosa.fft_frequencies(sr=sr)
low = S[freqs < 150].sum(0); low = low / low.max()
bf = np.minimum(librosa.time_to_frames(bt, sr=sr, hop_length=HOP), len(low) - 1)
score = []
for ph in range(4):
    idx = bf[ph::4]
    score.append(float(low[idx].mean() + oenv[idx].mean() / oenv.max()))
phase = int(np.argmax(score))
down = bt[phase::4]
bars = [{"mesure": i + 1, "debut_s": round(float(t), 3)} for i, t in enumerate(down)]

# ---------- sections par auto-similarité (chroma + MFCC, synchronisés sur les mesures) ----------
chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=HOP)
mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=HOP, n_mfcc=20)
df = librosa.time_to_frames(down, sr=sr, hop_length=HOP)
cs = librosa.util.sync(chroma, df, aggregate=np.median)[:, 1:-1]   # une colonne par mesure
ms = librosa.util.sync(mfcc, df, aggregate=np.mean)[:, 1:-1]
def z(a): return (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-9)
feat = np.vstack([z(cs), z(ms)])
fn = feat / (np.linalg.norm(feat, axis=0, keepdims=True) + 1e-9)
SSM = fn.T @ fn
NB = SSM.shape[0]; bar_t = np.append(down[:NB], down[NB] if len(down) > NB else dur)
def novelty(K):
    g = np.outer(sg.windows.gaussian(2 * K, K / 2), sg.windows.gaussian(2 * K, K / 2))
    ck = g * np.block([[np.ones((K, K)), -np.ones((K, K))], [-np.ones((K, K)), np.ones((K, K))]])
    P = np.pad(SSM, K, mode="edge")
    v = np.maximum(np.array([np.sum(P[i:i + 2 * K, i:i + 2 * K] * ck) for i in range(NB)]), 0)
    return v / (v.max() + 1e-9)
def cut_into(nov, h, dist):
    pk, _ = sg.find_peaks(nov, height=h, distance=dist)
    return pk, sorted(set([0] + list(pk) + [NB]))
nov = novelty(4); pk, bnd = cut_into(nov, 0.18, 4)
nov8 = novelty(8); pk8, bnd8 = cut_into(nov8, 0.25, 8)
# SSM renforcée le long des diagonales (4 mesures) : fait ressortir les passages répétés
R = np.zeros_like(SSM)
for L in range(4):
    R[: NB - L, : NB - L] += SSM[L:, L:]
R /= 4
off = R[np.triu_indices(NB, 4)]; thr_rep = float(np.mean(off) + 1.8 * np.std(off))
# répétitions : pour chaque décalage, suites d'au moins 4 mesures au-dessus du seuil
reps = []
for lag in range(4, NB):
    dg = np.array([R[i, i + lag] for i in range(NB - lag)]) > thr_rep
    lab, k = nd.label(dg)
    for j in range(1, k + 1):
        ii = np.where(lab == j)[0]
        if len(ii) >= 2:  # 2 départs consécutifs x 4 mesures de renfort = au moins 5 mesures qui se répètent
            a0, a1 = int(ii[0]), int(ii[-1]) + 3
            reps.append({"mesures": [a0 + 1, min(a1, NB - lag - 1) + 1], "repetees_en": [a0 + lag + 1, min(a1 + lag, NB - 1) + 1],
                         "t": [round(float(bar_t[a0]), 2), round(float(bar_t[a0 + lag]), 2)], "longueur_mesures": min(a1, NB - lag - 1) - a0 + 1})
reps.sort(key=lambda r: -r["longueur_mesures"])
def make_secs(bnd):
    out = []
    for a, b in zip(bnd[:-1], bnd[1:]):
        out.append({"debut_s": round(float(bar_t[a]), 2), "fin_s": round(float(bar_t[b]), 2), "mesures": [int(a) + 1, int(b)]})
    return out
secs = make_secs(bnd); secs8 = make_secs(bnd8)
# étiquetage : deux sections portent la même lettre si elles s'alignent sur une diagonale répétée
def seg_sim(s1, s2):
    a1, b1 = s1["mesures"][0] - 1, s1["mesures"][1]; a2, b2 = s2["mesures"][0] - 1, s2["mesures"][1]
    L = min(b1 - a1, b2 - a2); best = 0
    for sh in (-1, 0, 1):
        vals = [SSM[a1 + i, a2 + i + sh] for i in range(L) if 0 <= a2 + i + sh < NB]
        if vals: best = max(best, float(np.mean(vals)))
    return best, abs((b1 - a1) - (b2 - a2))
def label(secs):
    labs = []
    for i, s in enumerate(secs):
        cand = [(seg_sim(s, secs[j])[0], j) for j in range(i) if seg_sim(s, secs[j])[1] <= 2]
        cand = [c for c in cand if c[0] > thr_rep]
        labs.append(labs[max(cand)[1]] if cand else chr(65 + len(set(labs))))
    for s, l in zip(secs, labs):
        s["etiquette"] = l
label(secs); label(secs8)
for s in secs + secs8:
    m = (e_t >= s["debut_s"]) & (e_t < s["fin_s"]); s["energie_moy"] = round(float(e_v[m].mean()), 3) if m.any() else 0.0

# ---------- onsets et accents majeurs ----------
on = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, hop_length=HOP, units="time", backtrack=False)
on = on[on < cut_t + 0.05]
# accent = saut d'énergie à court terme (0,2 s après vs 1 s avant) combiné à l'attaque
sm = nd.uniform_filter1d(rms_n, int(0.2 * fps))
lag = int(1.0 * fps)

before = np.array([rms_n[max(0, i - lag): i].mean() if i > 0 else 0 for i in range(len(rms_n))])
after = np.array([rms_n[i: i + int(0.3 * fps)].mean() for i in range(len(rms_n))])
jump = after - before
acc = []
for i in sg.find_peaks(jump, height=0.18, distance=int(3 * fps))[0]:
    acc.append({"t": round(float(t_rms[i]), 2), "type": "impact/reprise", "saut": round(float(jump[i]), 2)})
for i in sg.find_peaks(-jump, height=0.18, distance=int(3 * fps))[0]:
    acc.append({"t": round(float(t_rms[i]), 2), "type": "chute/arret", "saut": round(float(jump[i]), 2)})
acc.sort(key=lambda a: a["t"])
def snap(t):  # temps le plus proche
    j = int(np.argmin(np.abs(bt - t))); return round(float(bt[j]), 3), round(float(t - bt[j]), 3)
for a in acc:
    a["temps_proche"], a["ecart"] = snap(a["t"]); k = int(np.argmin(np.abs(bt - a["temps_proche"])))
    a["temps_dans_mesure"] = int((k - phase) % 4) + 1; a["mesure"] = int((k - phase) // 4) + 1

# ---------- voix (APPROXIMATIF) : énergie harmonique 300-3400 Hz relative ----------
H, Pp = librosa.decompose.hpss(S, margin=3.0)
band = (freqs > 300) & (freqs < 3400)
hv = H[band].sum(0) / (S.sum(0) + 1e-9)
flat = librosa.feature.spectral_flatness(S=H)[0]
v = nd.uniform_filter1d(hv * (1 - flat), int(1.0 * fps))
vt = (v - np.percentile(v, 10)) / (np.percentile(v, 95) - np.percentile(v, 10))
vox = vt > 0.55
vox = nd.binary_opening(nd.binary_closing(vox, iterations=int(1.5 * fps)), iterations=int(1.0 * fps))
lab, n = nd.label(vox)
voice = []
for k in range(1, n + 1):
    ii = np.where(lab == k)[0]
    voice.append({"debut_s": round(float(t_rms[ii[0]]), 1), "fin_s": round(float(t_rms[ii[-1]]), 1)})

# ---------- sortie ----------
res = {
    "source": SRC, "duree_s": round(dur, 3), "coupure_finale_s": round(cut_t, 3), "coupure_debut_chute_s": round(cut_start, 2), "coupure_silence_-40dB_s": round(cut_silence, 2),
    "niveau_apres_coupure_dB": round(tail_db, 1),
    "tempo": tempo_check, "temps_s": [round(float(t), 4) for t in bt], "temps_bruts_s": [round(float(t), 4) for t in ref],
    "temps_note": "temps détectés à 5,8 ms, recalés sur l'attaque, lissés sur ±4 temps. Le tempo varie : ne pas utiliser de grille fixe.",
    "intervalle_temps_s": {"moyenne": round(float(ibi.mean()), 5), "median": round(float(np.median(ibi)), 5), "ecart_type": round(float(np.std(ibi)), 5), "min": round(float(ibi.min()), 4), "max": round(float(ibi.max()), 4)},
    "phase_premier_temps_de_mesure": phase, "score_phases": [round(s, 3) for s in score],
    "mesures": bars, "sections_grandes": secs8, "sections_fines": secs, "repetitions": reps[:25], "seuil_repetition": round(thr_rep, 3),
    "energie": {"pas_s": step, "valeurs": [round(float(x), 3) for x in e_v]},
    "onsets_s": [round(float(t), 3) for t in on], "accents": acc,
    "voix_APPROXIMATIF": voice,
}
json.dump(res, open(OUT + "analysis.json", "w"), ensure_ascii=False, indent=1)
np.save(OUT + "ssm.npy", SSM)

# ---------- graphique ----------
fig, ax = plt.subplots(3, 1, figsize=(22, 16), gridspec_kw={"height_ratios": [3, 1, 5]})
a = ax[0]
cols = plt.cm.tab10(np.linspace(0, 1, 10))
for s in secs8:
    a.axvspan(s["debut_s"], s["fin_s"], color=cols[(ord(s["etiquette"]) - 65) % 10], alpha=0.18)
    a.text((s["debut_s"] + s["fin_s"]) / 2, 1.08, s["etiquette"], ha="center", fontsize=11, weight="bold")
for d in down: a.axvline(d, color="0.75", lw=0.5)
a.plot(t_rms, nd.uniform_filter1d(rms_n, 5), color="0.6", lw=0.5)
a.plot(e_t + step / 2, e_v, color="k", lw=1.6, label="énergie (RMS rel., 2/s)")
for ac_ in acc:
    a.axvline(ac_["t"], color="tab:red" if ac_["type"] != "chute/arret" else "tab:blue", lw=1.2, ls="--")
a.axvline(cut_start, color="m", lw=2, label=f"coupure : chute {cut_start:.2f} s, silence {cut_silence:.2f} s")
for s in secs: a.axvline(s["debut_s"], ymin=0.93, ymax=1, color="k", lw=1)
for vv in voice: a.axvspan(vv["debut_s"], vv["fin_s"], ymin=0, ymax=0.04, color="tab:green")
a.set_xlim(0, dur); a.set_ylim(0, 1.15); a.set_xticks(np.arange(0, dur, 10))
a.set_xticklabels([f"{int(t//60)}:{int(t%60):02d}" for t in np.arange(0, dur, 10)])
a.legend(loc="lower left"); a.set_title(f"You Know My Name — {tempo:.1f} BPM, {len(down)} mesures, coupure {cut_t:.2f} s  (rouge=impact, bleu=chute, vert=voix approx.)")
ax[1].plot(bar_t[:NB], nov, color="0.5", label="nouveauté 4 mesures"); ax[1].plot(bar_t[:NB], nov8, color="k", label="nouveauté 8 mesures")
ax[1].set_xlim(0, dur); ax[1].legend(loc="upper right")
for p in pk8: ax[1].axvline(bar_t[p], color="tab:red", lw=0.8)
ax[2].imshow(R, cmap="magma", aspect="equal", origin="lower", extent=[0.5, NB + 0.5, 0.5, NB + 0.5]); ax[2].set_title("auto-similarité renforcée (chroma + MFCC, par mesure) : les diagonales = passages répétés"); ax[2].set_xlabel("mesure")
plt.tight_layout(); plt.savefig(OUT + "carte.png", dpi=80)

# ---------- tableau lisible ----------
def mmss(t): return f"{int(t//60)}:{t%60:05.2f}"
L = [f"# Carte du morceau\n", f"- Durée : {dur:.3f} s ({mmss(dur)})", f"- Tempo : {tempo:.2f} BPM (1 temps = {60/tempo:.4f} s, 1 mesure = {240/tempo:.3f} s)",
     f"- Temps détectés : {len(bt)} ; premier temps : {bt[0]:.3f} s ; mesures : {len(down)} ; premier temps de mesure : {down[0]:.3f} s",
     f"- Coupure finale : chute à {cut_start:.2f} s ({mmss(cut_start)}), silence (-40 dB) à {cut_silence:.2f} s ({mmss(cut_silence)}) ; niveau ensuite : {tail_db:.1f} dB sous la moyenne", "",
     "## Grandes sections (noyau 8 mesures)", "| # | étiquette | début | fin | mesures | énergie |", "|---|---|---|---|---|---|"]
for i, s in enumerate(secs8): L.append(f"| {i+1} | {s['etiquette']} | {mmss(s['debut_s'])} | {mmss(s['fin_s'])} | {s['mesures'][0]}-{s['mesures'][1]} | {s['energie_moy']:.2f} |")
L += ["", "## Sections fines (noyau 4 mesures)", "| # | étiquette | début | fin | mesures | énergie |", "|---|---|---|---|---|---|"]
for i, s in enumerate(secs): L.append(f"| {i+1} | {s['etiquette']} | {mmss(s['debut_s'])} | {mmss(s['fin_s'])} | {s['mesures'][0]}-{s['mesures'][1]} | {s['energie_moy']:.2f} |")
L += ["", "## Passages répétés (les plus longs)", "| mesures | répétées en | longueur (mesures) |", "|---|---|---|"]
for r_ in reps[:12]: L.append(f"| {r_['mesures'][0]}-{r_['mesures'][1]} ({mmss(r_['t'][0])}) | {r_['repetees_en'][0]}-{r_['repetees_en'][1]} ({mmss(r_['t'][1])}) | {r_['longueur_mesures']} |")
L += ["", "## Accents majeurs", "| t | type | mesure | temps n° | temps le plus proche (s) | écart (s) |", "|---|---|---|---|---|---|"]
for a_ in acc: L.append(f"| {mmss(a_['t'])} | {a_['type']} | {a_['mesure']} | {a_['temps_dans_mesure']} | {a_['temps_proche']:.3f} | {a_['ecart']:+.3f} |")
L += ["", "## Voix (APPROXIMATIF, non vérifié)", ", ".join(f"{mmss(v['debut_s'])}-{mmss(v['fin_s'])}" for v in voice),
      "", "## Mesures", "| mesure | début (s) | mesure | début (s) | mesure | début (s) | mesure | début (s) |", "|---|---|---|---|---|---|---|---|"]
for i in range(0, len(bars), 4):
    L.append("| " + " | ".join(f"{b['mesure']} | {b['debut_s']:.3f}" for b in bars[i:i + 4]) + " |")
open(OUT + "mesures.md", "w").write("\n".join(L) + "\n")
res["tempo"] = {k: v for k, v in res["tempo"].items()}
print(json.dumps({k: (res[k] if k != "tempo" else {a: b for a, b in res[k].items() if a != "tempo_local_16_temps"}) for k in ["duree_s", "coupure_debut_chute_s", "coupure_silence_-40dB_s", "niveau_apres_coupure_dB", "tempo", "intervalle_temps_s", "phase_premier_temps_de_mesure", "score_phases"]}, ensure_ascii=False, indent=1))
print("temps[:6]", res["temps_s"][:6], "nb temps", len(bt), "nb mesures", len(down))
for s in secs8: print(s)
for r_ in reps[:12]: print(r_)
for a_ in acc: print(a_)
print("voix", voice)
