"""Bake the original choreography into a portable browser player and 1080p MP4.
Run: python render.py --ffmpeg PATH_TO_FFMPEG
Dependencies: pillow, numpy. Animation credit: yym8224961.
"""
from pathlib import Path
import argparse, base64, gzip, io, json, math, shutil, subprocess, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from engine import Film, cw

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'
BUILD.mkdir(exist_ok=True)
W,H,FPS=128,44,24
CW,CH=14,22
COLORS=['#af875f','#ffaf5f','#ffdf5f','#ffffd7','#ff5f5f','#875f00','#5f5f00']
BG='#070909'
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',22)
bold=ImageFont.truetype('C:/Windows/Fonts/consolab.ttf',22)
cjk=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20)
symbols=ImageFont.truetype('C:/Windows/Fonts/seguisym.ttf',20)
tiles=[Image.new('RGB',(CW,CH),BG)]
ids={(' ',0):[0]}

def glyph(ch,style):
    if not ch or ch==' ':return [0]
    key=(ch,style)
    if key in ids:return ids[key]
    n=max(1,cw(ch)); im=Image.new('RGB',(CW*n,CH),BG)
    d=ImageDraw.Draw(im); f=(cjk if cw(ch)==2 else symbols) if ord(ch)>127 else (bold if style in (2,3,4) else font)
    box=d.textbbox((0,0),ch,font=f); tw=box[2]-box[0]; th=box[3]-box[1]
    # Keep a fixed baseline for ASCII; vertically center ideographs.
    yy=-1 if ord(ch)<128 else (CH-th)//2-box[1]
    d.text(((CW*n-tw)//2-box[0],yy),ch,font=f,fill=COLORS[style])
    found=[]
    for k in range(n):
        found.append(len(tiles));tiles.append(im.crop((k*CW,0,(k+1)*CW,CH)))
    ids[key]=found;return found

def frame_cells(canvas):
    result=np.zeros((H,W),dtype='<u2')
    for y,row in enumerate(canvas.cells):
        for x,(ch,s) in enumerate(row):
            if not ch:continue
            gs=glyph(ch,s)
            for k,g in enumerate(gs):
                if x+k<W:result[y,x+k]=g
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--ffmpeg');ap.add_argument('--samples-only',action='store_true');args=ap.parse_args()
    if not args.ffmpeg:
        args.ffmpeg=shutil.which('ffmpeg')
        if not args.ffmpeg:
            import imageio_ffmpeg
            args.ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    if not args.samples_only:
        subprocess.run([args.ffmpeg, '-y', '-v', 'error', '-i', str(ROOT/'media/song.mp3'),
                        '-map', '0:a:0', '-ac', '2', '-ar', '44100', '-c:a', 'pcm_s16le',
                        str(ROOT/'media/song.wav')], check=True)
    film=Film();duration=film.config['duration'];count=math.ceil(duration*FPS)
    samples=[1,24,31,35,39,57,65,81,93,108,115,132,152,168,182,199]
    if args.samples_only:
        for t in samples:
            cells=frame_cells(film.render(t,W,H));a=np.array(tiles,dtype=np.uint8)[cells].transpose(0,2,1,3,4).reshape(H*CH,W*CW,3)
            Image.fromarray(a).save(ROOT/f'sample-{t}.png')
        return
    start=time.monotonic();frames=np.zeros((count,H,W),dtype='<u2')
    for i in range(count):
        frames[i]=frame_cells(film.render(i/FPS,W,H))
        if i%480==0:print(f'BAKE {i}/{count} elapsed={time.monotonic()-start:.1f}s',flush=True)
    (ROOT/'frames.bin.gz').write_bytes(gzip.compress(frames.tobytes(),compresslevel=6))
    atlas=Image.new('RGB',(CW*64,CH*math.ceil(len(tiles)/64)),BG)
    for i,tile in enumerate(tiles):atlas.paste(tile,((i%64)*CW,(i//64)*CH))
    atlas.save(ROOT/'atlas.png')
    meta={'width':W,'height':H,'cellWidth':CW,'cellHeight':CH,'fps':FPS,'frames':count,'duration':duration,'glyphs':len(tiles)}
    (ROOT/'animation.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    template=(ROOT/'source/player-template.html').read_text(encoding='utf-8')
    template=template.replace('__META__',json.dumps(meta)).replace('__FRAMES__',base64.b64encode((ROOT/'frames.bin.gz').read_bytes()).decode()).replace('__ATLAS__',base64.b64encode((ROOT/'atlas.png').read_bytes()).decode()).replace('__AUDIO__',base64.b64encode((ROOT/'media/song.mp3').read_bytes()).decode())
    (BUILD/'world.execute(me)-ASCII.html').write_text(template,encoding='utf-8')
    print(f'HTML READY glyphs={len(tiles)} compressed={(ROOT/"frames.bin.gz").stat().st_size}',flush=True)
    lut=np.array(tiles,dtype=np.uint8)
    cmd=[args.ffmpeg,'-y','-loglevel','warning','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W*CW}x{H*CH}','-r',str(FPS),'-i','pipe:0','-i',str(ROOT/'media/song.mp3'),'-vf','pad=1920:1080:64:56:color=0x070909','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(duration),'-movflags','+faststart',str(BUILD/'world.execute(me)-ASCII.mp4')]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i,cells in enumerate(frames):
        a=lut[cells].transpose(0,2,1,3,4).reshape(H*CH,W*CW,3)
        if i in [int(t*FPS) for t in samples]:
            im=Image.new('RGB',(1920,1080),BG);im.paste(Image.fromarray(a),(64,56));im.save(ROOT/f'sample-{int(i/FPS)}.png')
        proc.stdin.write(a.tobytes())
        if i%480==0:print(f'ENCODE {i}/{count} elapsed={time.monotonic()-start:.1f}s',flush=True)
    proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('ffmpeg failed')
    print(f'DONE {count} frames in {time.monotonic()-start:.1f}s',flush=True)

if __name__=='__main__':main()
