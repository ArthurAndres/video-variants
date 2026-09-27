"""Rendu : python3 -m engine.render T0 T1 sortie.mp4 [--preview] [--jobs 4] [--only NOM_DE_PLAN]
- renderFrame(t) pur et déterministe ; images envoyées à ffmpeg par un pipe (rawvideo rgb24) ;
- parallélisation par tranches contiguës sur les cœurs, puis concaténation sans ré-encodage ;
- audio : la portion correspondante du MP3, inchangée (AAC 320 kb/s)."""
import sys, os, subprocess, time, argparse, multiprocessing as mp
import numpy as np
from engine import core
from engine.timeline import SHOTS, shot_at

def render_frame(surface, t):
    c = surface.getCanvas(); c.clear(core.col(core.INK))
    sh, lt = shot_at(t)
    if sh is not None:
        c.save(); sh["fn"](c, lt, sh["_dur"], t, sh); c.restore()
    return core.finish(core.snapshot_rgb(surface), t, grain=sh.get("grain", 0.03) if sh else 0.03)

def worker(args):
    f0, f1, path, scale = args
    surf = core.new_surface()
    w, h = (core.W // scale, core.H // scale)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{core.W}x{core.H}",
                           "-r", str(core.FPS), "-i", "-", "-vf", f"scale={w}:{h}:flags=area" if scale > 1 else "null",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17" if scale == 1 else "22", "-pix_fmt", "yuv420p", path],
                          stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(f0, f1):
        ff.stdin.write(render_frame(surf, f / core.FPS).tobytes())
    ff.stdin.close(); ff.wait()
    return f1 - f0, time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("t0", type=float); ap.add_argument("t1", type=float); ap.add_argument("out")
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    f0, f1 = int(round(a.t0 * core.FPS)), int(round(a.t1 * core.FPS))
    scale = 2 if a.preview else 1
    n = max(1, min(a.jobs, (f1 - f0) // 15))
    cuts = np.linspace(f0, f1, n + 1).astype(int)
    tmp = a.out + ".parts"; os.makedirs(tmp, exist_ok=True)
    jobs = [(int(cuts[i]), int(cuts[i + 1]), f"{tmp}/p{i:02d}.mp4", scale) for i in range(n)]
    t0 = time.time()
    with mp.Pool(n) as pool: res = pool.map(worker, jobs)
    with open(f"{tmp}/list.txt", "w") as fh:
        for j in jobs: fh.write(f"file '{os.path.abspath(j[2])}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                    "-ss", f"{a.t0:.3f}", "-t", f"{a.t1 - a.t0:.3f}", "-i", os.path.join(core.ROOT, "references/you_know_my_name.mp3"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-shortest", a.out], check=True)
    frames = sum(r[0] for r in res); dt = time.time() - t0
    print(f"{frames} images en {dt:.1f} s ({frames / dt:.1f} img/s, {n} processus) -> {a.out}")

if __name__ == "__main__":
    main()
