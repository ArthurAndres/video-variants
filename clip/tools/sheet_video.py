"""Planche-contact d'une vidéo : python3 tools/sheet_video.py video.mp4 sortie.jpg [t0] [t1] [pas]"""
import sys, subprocess, numpy as np, cv2
v, out = sys.argv[1], sys.argv[2]
t0 = float(sys.argv[3]) if len(sys.argv) > 3 else 0; t1 = float(sys.argv[4]) if len(sys.argv) > 4 else 1e9; st = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v], capture_output=True, text=True).stdout)
t1 = min(t1, dur - 0.01); tiles = []
for t in np.arange(t0, t1, st):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", v, "-frames:v", "1", "-vf", "scale=384:216", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    im = np.frombuffer(raw, np.uint8).reshape(216, 384, 3).copy()
    cv2.rectangle(im, (0, 0), (62, 20), (0, 0, 0), -1); cv2.putText(im, f"{t:.1f}", (3, 15), 0, 0.5, (255, 255, 255), 1); tiles.append(im)
while len(tiles) % 5: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 5]) for i in range(0, len(tiles), 5)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
