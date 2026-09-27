"""Planche-contact : python3 tools/contact.py sortie.jpg t0 t1 [pas] -- images de references/test_frames (2/s), étiquetées en secondes."""
import sys, cv2, numpy as np
out, t0, t1 = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]); cols = 5; tw = 384
tiles = []
for t in np.arange(t0, t1, 0.5):
    im = cv2.imread(f"references/test_frames/f_{int(round(t*2))+1:03d}.jpg")
    if im is None: continue
    im = cv2.resize(im, (tw, tw * 9 // 16), interpolation=cv2.INTER_AREA)
    cv2.rectangle(im, (0, 0), (70, 22), (0, 0, 0), -1); cv2.putText(im, f"{t:.1f}", (4, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    tiles.append(im)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
