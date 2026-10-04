"""Prepare pinned external dependencies locally; no third-party media is bundled."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def download(url, target, expected):
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
        return
    request = urllib.request.Request(url, headers={'User-Agent': 'world-execute-ascii-crt'})
    with urllib.request.urlopen(request, timeout=45) as response:
        data = response.read()
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f'Checksum mismatch: {target.name}; expected {expected}, got {actual}')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)

def setup_animation(lock):
    upstream = ROOT / '.cache/upstream'
    for name, digest in lock['files'].items():
        url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{name}"
        download(url, upstream / name, digest)
    source = ROOT / 'source'
    player = (upstream / 'player.py').read_text(encoding='utf-8')
    engine = player[:player.index('class Audio:')]
    engine = engine.replace('import sys, termios, threading, time, tty, unicodedata',
                            'import sys, threading, time, unicodedata')
    engine = engine.replace('.read_text()', '.read_text(encoding="utf-8")')
    engine = engine.replace("hint='SPACE play/pause   <- -> 5s   R restart   Q quit   H help'",
                            "hint='MILI / world.execute(me);    ASCII ANIMATION / yym8224961'")
    compile(engine, 'engine.py', 'exec')
    (source / 'engine.py').write_text(engine, encoding='utf-8')
    for name in ['scenes.py', 'config.json', 'lyrics.json', 'spectrum.json']:
        shutil.copy2(upstream / name, source / name)
    print('Animation dependency ready at pinned commit ' + lock['commit'], flush=True)

def setup_terminal(lock):
    terminal = lock['terminal']
    archive = ROOT / '.cache/windows-terminal-x64.zip'
    download(terminal['url'], archive, terminal['sha256'])
    if archive.stat().st_size != terminal['bytes']:
        raise RuntimeError('Windows Terminal archive size mismatch')
    target = ROOT / 'terminal-runtime'
    target.mkdir(exist_ok=True)
    runtime = target / ('terminal-' + terminal['tag'].removeprefix('v'))
    if not (runtime / 'WindowsTerminal.exe').is_file():
        with zipfile.ZipFile(archive) as bundle:
            for entry in bundle.infolist():
                if not (target / entry.filename).resolve().is_relative_to(target.resolve()):
                    raise RuntimeError('Unsafe archive path')
            bundle.extractall(target)
    if not (runtime / 'WindowsTerminal.exe').is_file():
        raise RuntimeError('Portable Terminal executable missing')
    (runtime / '.portable').touch()
    directory = runtime / 'settings'
    directory.mkdir(exist_ok=True)
    config = directory / 'settings.json'
    # Preserve appearance edits on subsequent setup runs.
    if not config.exists():
        profile = json.loads((ROOT / 'crt-profile.json').read_text(encoding='utf-8'))
        settings = {'$schema': 'https://aka.ms/terminal-profiles-schema',
                    'defaultProfile': profile['guid'], 'initialCols': 128, 'initialRows': 44,
                    'launchMode': 'maximized', 'theme': 'dark', 'alwaysShowTabs': False,
                    'copyOnSelect': False, 'profiles': {'defaults': {}, 'list': [profile]}}
        config.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Portable CRT Terminal ready: ' + str(runtime), flush=True)

def main():
    parser = argparse.ArgumentParser(description='Download checksum-pinned animation source and Microsoft Windows Terminal')
    parser.add_argument('--skip-terminal', action='store_true', help='Prepare animation only; use an existing terminal')
    args = parser.parse_args()
    lock = json.loads((ROOT / 'dependencies.lock.json').read_text(encoding='utf-8'))
    setup_animation(lock)
    if not args.skip_terminal:
        setup_terminal(lock)
    (ROOT / 'media').mkdir(exist_ok=True)
    print('Next: provide media/song.wav, then run run-crt-terminal.cmd. Silent preview: run-crt-terminal.cmd --silent')

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Setup failed: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
