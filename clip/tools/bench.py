import skia, numpy as np, time, subprocess, sys
W,H=int(sys.argv[1]),int(sys.argv[2]); N=60
surf=skia.Surface(W,H); c=surf.getCanvas()
p=skia.Paint(AntiAlias=True,Style=skia.Paint.kStroke_Style,StrokeWidth=1.2)
ff=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r','30','-i','-','-c:v','libx264','-preset','medium','-crf','17','/tmp/bench.mp4'],stdin=subprocess.PIPE)
t0=time.time()
for f in range(N):
    c.clear(skia.Color(240,228,200))
    p.setColor(skia.Color(22,16,13))
    for i in range(0,H,3): c.drawLine(0,i,W,i+30*np.sin(f*.1+i*.01),p)  # 1 ligne/3px, ~gravure
    c.drawCircle(W/2,H/2,H/4,skia.Paint(AntiAlias=True,Color=skia.Color(246,184,72)))
    a=surf.makeImageSnapshot().toarray()
    if f==0: print('pixel or (246,184,72) lu comme', a[H//2,W//2][:3], '-> ordre', 'BGRA' if a[H//2,W//2][0]==72 else 'RGBA')
    ff.stdin.write(np.ascontiguousarray(a[...,[2,1,0]] if a[H//2,W//2][0]==72 else a[...,:3]).tobytes())
ff.stdin.close(); ff.wait()
print(f'{W}x{H}: {N/(time.time()-t0):.1f} img/s (rendu gravure plein écran + encodage x264, 1 cœur)')
