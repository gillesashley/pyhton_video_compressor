import os
import sys
import subprocess
import urllib.request
import zipfile

def download_and_extract(url, dest_zip, extract_to):
    print('Downloading FFmpeg...')
    urllib.request.urlretrieve(url, dest_zip)
    print('Extracting FFmpeg...')
    with zipfile.ZipFile(dest_zip, 'r') as z:
        z.extractall(extract_to)
    os.remove(dest_zip)

def find_bin_dir(extract_to):
    entries = [os.path.join(extract_to, d) for d in os.listdir(extract_to) if os.path.isdir(os.path.join(extract_to, d))]
    if not entries:
        return None
    # Prefer folder that contains a 'bin' subfolder
    for e in entries:
        b = os.path.join(e, 'bin')
        if os.path.isdir(b):
            return b
    # fallback to first entry's bin
    return os.path.join(entries[0], 'bin')

def main():
    cwd = os.getcwd()
    ff_dir = os.path.join(cwd, 'ffmpeg')
    zip_path = os.path.join(cwd, 'ffmpeg.zip')
    if not os.path.isdir(ff_dir) or not os.listdir(ff_dir):
        url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
        try:
            download_and_extract(url, zip_path, ff_dir)
        except Exception as e:
            print('Failed to download or extract FFmpeg:', e, file=sys.stderr)
            sys.exit(2)

    bin_dir = find_bin_dir(ff_dir)
    if not bin_dir or not os.path.exists(os.path.join(bin_dir, 'ffmpeg.exe')):
        print('ffmpeg.exe not found after extraction. Looked in:', bin_dir, file=sys.stderr)
        sys.exit(3)

    print('Using FFmpeg from:', bin_dir)
    env = os.environ.copy()
    env['PATH'] = bin_dir + os.pathsep + env.get('PATH', '')

    # Run main.py with the same Python interpreter (will use venv if invoked from venv python)
    python_exe = sys.executable
    print('Running main.py with:', python_exe)
    proc = subprocess.run([python_exe, 'main.py'], cwd=cwd, env=env)
    sys.exit(proc.returncode)

if __name__ == '__main__':
    main()
