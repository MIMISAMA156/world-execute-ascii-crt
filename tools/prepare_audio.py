"""Convert the user's audio to the PCM format required by Windows waveOut."""
from pathlib import Path
import argparse
import shutil
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[1]

def validate(path):
    with wave.open(str(path), 'rb') as audio:
        if (audio.getnchannels(), audio.getframerate(), audio.getsampwidth(), audio.getcomptype()) != (2, 44100, 2, 'NONE'):
            raise ValueError('Expected stereo 44100 Hz 16-bit uncompressed PCM WAV')
        return audio.getnframes() / audio.getframerate()

def main():
    parser = argparse.ArgumentParser(description='Prepare your own audio for the terminal player')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--ffmpeg', help='FFmpeg executable; otherwise use PATH or imageio-ffmpeg')
    args = parser.parse_args()
    target = ROOT / 'media/song.wav'
    target.parent.mkdir(exist_ok=True)
    try:
        duration = validate(args.input)
        if args.input.resolve() != target.resolve():
            shutil.copy2(args.input, target)
    except (wave.Error, EOFError, ValueError):
        ffmpeg = args.ffmpeg or shutil.which('ffmpeg')
        if not ffmpeg:
            try:
                import imageio_ffmpeg
                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except ImportError:
                parser.error('FFmpeg not found. Specify --ffmpeg or install imageio-ffmpeg.')
        subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', str(args.input),
                        '-map', '0:a:0', '-ac', '2', '-ar', '44100', '-c:a', 'pcm_s16le', str(target)], check=True)
        duration = validate(target)
    print(f'Audio ready: {target}; duration={duration:.3f}s')
    if not 210 < duration < 214:
        print('This timeline expects the approximately 211.907 second version; other edits may drift.')

if __name__ == '__main__':
    main()
