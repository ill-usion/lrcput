# Audio Lyrics Fetching and Embedding Script (lrcput.py)

The `lrcput.py` script allows you to embed lyrics into FLAC, M4A and MP3 audio files. It supports specifying a directory containing the audio files and subdirectories containing audio files.

**this script was designed to embed lyrics acquired from [lrclib](https://lrclib.net)**

## Requirements

- Python 3.x
- Required Python libraries (install using `pip install` or `pip install -r requirements.txt`):
  - requests
  - urllib3
  - eyed3
  - mutagen
  - tqdm

## Usage

1. Open a terminal or command prompt.

2. Navigate to the directory where the script `lrcput.py` is located.

3. Run the script with the following command to fetch and embed lyrics:

   ```sh
   python lrcput.py -d "path/to/your/directory" -s -R
   ```

Replace "path/to/your/directory" with the actual path to the directory containing your audio files.

    -d or --directory: Specify the directory containing audio files.
    -s or --skip: Optional. Skip files that already have embedded lyrics.
    -R or --recursive: Optional. Recursively process subdirectories
    -i or --ignore-hashed: On by default. Skip already processed/hashed files. Good for re-running the script on the same directory with new files.

## Example

Suppose you have the following directory structure:

```audio_directory/
|-- song1.flac
|-- song2.mp3
|-- song3.m4a
|-- More music
    |-- song4.flac
    |-- song5.flac
    |-- ...
|-- ...
```

To embed lyrics into the audio files, navigate to the script's directory and run the following command:

```
python lrcput.py -d "path/to/audio_directory" -s -R
```

## Notes

- You can modify the script's options andbehavior by editing the script directly.

- Make sure to backup your original audiofiles before running the script.

- To clear the hashed files list, delete the `.lrcput-hash` file in the script directory. You may need to enable show hidden files in your file explorer.  
## Acknowledgments

This script utilizes the mutagen and eyed3 libraries for working with audio and metadata. Additionally, it utilizes [lrclib](https://lrclib.net) to fetch the lyrics.