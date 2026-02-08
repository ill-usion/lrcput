import os
import eyed3
import shutil
import argparse
import requests
import hashlib
from urllib.parse import urlencode
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from tqdm import tqdm

LRCPUT_VERSION = "0.1.1"

def md5_checksum(filepath):
    with open(filepath, "rb") as file:
        digest = hashlib.file_digest(file, "md5")
        return digest.hexdigest()

def get_checked_hashes(hashes_filepath):
    try:
        with open(hashes_filepath, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        return []

def write_hashes(hashes_filepath, hashes):
    with open(hashes_filepath, "w") as file:
        file.write("\n".join(hashes))

def append_hash(hashes_filepath, _hash):
    with open(hashes_filepath, "a+") as file:
        file.write("\n")
        file.write(_hash)

def fetch_lyrics(track_name, artist_name, album_name, duration):
    params = {
        "track_name": track_name,
        "artist_name": artist_name,
        "album_name": album_name,
        "duration": duration
    }
    
    headers = {
        "User-Agent": f"LRCPUT v{LRCPUT_VERSION} github.com/ill-usion/lrcput"
    }

    url = f"https://lrclib.net/api/get?{urlencode(params)}"
    req = requests.get(url, headers=headers)

    if not req.ok:
        return None
    
    resp = req.json()
    return resp["plainLyrics"] if resp["syncedLyrics"] == None else resp["syncedLyrics"]

def has_embedded_lyrics(audio):
    if isinstance(audio, FLAC):
        return 'LYRICS' in audio
    elif isinstance(audio, MP4):
        return '\xa9lyr' in audio.tags
    elif isinstance(audio, eyed3.core.AudioFile):
        return audio.tag.lyrics is not None
    return False

def embed_lrc(directory, skip_existing, recursive, ignore_hashed):
    total_audio_files = 0
    embedded_lyrics_files = 0
    failed_files = []
    HASHES_FILEPATH = "./.lrcput-hash"
    file_hashes = get_checked_hashes(HASHES_FILEPATH)

    audio_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.flac') or file.endswith('.mp3') or file.endswith('.m4a'):
                audio_files.append(os.path.join(root, file))
    
    with tqdm(total=len(audio_files), desc='Embedding LRC files', unit='file') as pbar:
        for audio_path in audio_files:
            file = os.path.basename(audio_path)
            checksum = md5_checksum(audio_path)

            if ignore_hashed and checksum and str(checksum) in file_hashes:
                pbar.set_postfix({"status": "skipped: hashed file"})
                pbar.update(1)
                continue
            
            append_hash(HASHES_FILEPATH, str(checksum))

            try:
                audio = None
                if file.endswith('.flac'):
                    audio = FLAC(audio_path)
                    track_name = audio["title"][0]
                    artist_name = audio["artist"][0]
                    album_name = audio["album"][0]
                    duration = audio.info.length
                elif file.endswith('.mp3'):
                    audio = eyed3.load(audio_path)
                    track_name = audio.tag.title
                    artist_name = audio.tag.artist
                    album_name = audio.tag.album
                    duration = audio.info.time_secs
                elif file.endswith('.m4a'):
                    audio = MP4(audio_path)
                    track_name = audio["title"][0]
                    artist_name = audio["artist"][0]
                    album_name = audio["album"][0]
                    duration = audio.info.length
                
                duration = round(duration)
            except:
                pbar.set_postfix({"status": "skipped: no metadata"})
                pbar.update(1)
                continue

            if skip_existing:
                if has_embedded_lyrics(audio):
                    pbar.set_postfix({"status": "skipped: contains lyrics"})
                    pbar.update(1)
                    continue

            lyrics = fetch_lyrics(track_name, artist_name, album_name, duration)
            
            if not lyrics:
                pbar.set_postfix({"status": "skipped: lyrics not found"})
                pbar.update(1)
                continue

            try:
                if file.endswith('.flac'):
                    audio['LYRICS'] = lyrics
                    audio.save()
                elif file.endswith('.mp3'):
                    tag = audio.tag
                    tag.lyrics.set(lyrics)
                    tag.save(version=eyed3.id3.ID3_V2_3)
                elif file.endswith('.m4a'):
                    audio.tags['\xa9lyr'] = lyrics
                    audio.save()
                
                embedded_lyrics_files += 1
                pbar.set_postfix({"status": f"embedded: {file}"})
                pbar.update(1)
                pbar.refresh()
            except Exception as e:
                print(f"Error embedding LRC for {file}: {str(e)}")
                pbar.set_postfix({"status": f"error: {file}"})
                pbar.update(1)
                pbar.refresh()
                failed_files.append(file)
                continue

    return len(audio_files), embedded_lyrics_files, failed_files

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Embed LRC files into audio files (FLAC, MP3, and M4A) and optionally reduce LRC files.')
    parser.add_argument('-d', '--directory', required=True, help='Directory containing audio and LRC files')
    parser.add_argument('-s', '--skip', action='store_true', help='Skip files that already have embedded lyrics')
    parser.add_argument('-R', '--recursive', action='store_true', help='Recursively process subdirectories')
    parser.add_argument('-i', '--ignore-hashed', action='store_true', default=True, help='Skip already processed/hashed files. Good for re-running the script on the same directory with new files.')
    args = parser.parse_args()
    
    banner = f"""
██╗     ██████╗  ██████╗██████╗ ██╗   ██╗████████╗
██║     ██╔══██╗██╔════╝██╔══██╗██║   ██║╚══██╔══╝
██║     ██████╔╝██║     ██████╔╝██║   ██║   ██║   
██║     ██╔══██╗██║     ██╔═══╝ ██║   ██║   ██║   
███████╗██║  ██║╚██████╗██║     ╚██████╔╝   ██║   
╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝      ╚═════╝    ╚═╝   
v{LRCPUT_VERSION}

Scripted by TheRedSpy15
Modified to fetch lyrics by ill-usion"""
    print(banner)

    directory_path = args.directory
    skip_existing = args.skip
    recursive = args.recursive
    ignore_hashed = args.ignore_hashed
    total, embedded, failed = embed_lrc(directory_path, skip_existing, recursive, ignore_hashed)
    percentage = (embedded / total) * 100 if total > 0 else 0
    
    print(f"Total audio files: {total}")
    print(f"Embedded lyrics in {embedded} audio files.")
    print(f"Percentage of audio files with embedded lyrics: {percentage:.2f}%")
    
    if failed:
        print("\nFailed to embed LRC for the following files:")
        for file in failed:
            print(file)
