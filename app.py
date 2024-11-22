import logging
from pathlib import Path
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TDRC
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
import acoustid
import musicbrainzngs
import argparse
from dotenv import load_dotenv
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

def load_config():
    """Load configuration from environment variables."""
    required_keys = {'ACOUSTID_KEY', 'ACOUSTID_NAME', 'ACOUSTID_VERSION', 'SCAN_DIRECTORY'}
    missing_keys = required_keys - set(os.environ.keys())
    if missing_keys:
        logging.critical(f"Missing required environment variables: {', '.join(missing_keys)}")
        exit(1)

    return {
        'acoustid_key': os.getenv('ACOUSTID_KEY'),
        'acoustid_name': os.getenv('ACOUSTID_NAME'),
        'acoustid_version': os.getenv('ACOUSTID_VERSION'),
        'scan_directory': os.getenv('SCAN_DIRECTORY')
    }

# Initialize MusicBrainz API
def init_musicbrainz(config):
    musicbrainzngs.set_useragent(config['acoustid_name'], config['acoustid_version'], config['acoustid_key'])

# Fetch metadata from MusicBrainz
def fetch_metadata_from_musicbrainz(musicbrainz_id):
    try:
        result = musicbrainzngs.get_recording_by_id(musicbrainz_id, includes=['releases'])
        logging.debug(f"MusicBrainz Results\n\n{result}\n\n")
        metadata = result['recording']

        title = metadata.get('title', 'Unknown Title')
        artist = metadata.get('artist-credit', [{'name': 'Unknown Artist'}])[0]['name']
        release = metadata.get('release-list', [{}])[0]
        album = release.get('title', 'Unknown Album')
        year = release.get('date', 'Unknown Year')[:4] if 'date' in release else 'Unknown Year'

        return {"title": title, "artist": artist, "album": album, "year": year}
    except musicbrainzngs.WebServiceError as e:
        logging.error(f"Error fetching metadata from MusicBrainz: {e}")
        return {"album": "Unknown Album", "year": "Unknown Year"}

# Get audio file metadata using Mutagen
def get_metadata_with_mutagen(file_path):
    try:
        if file_path.suffix == '.mp3':
            audio = MP3(file_path, ID3=ID3)
            tags = audio.tags
            logging.debug(f"Printing tags:\n{tags}\n")
            title = tags.get('TIT2').text[0] if 'TIT2' in tags else 'Unknown Title'
            artist = tags.get('TPE1').text[0] if 'TPE1' in tags else 'Unknown Artist'
            album = tags.get('TALB').text[0] if 'TALB' in tags else 'Unknown Album'

            # Check TDRC first, then fall back to TYER
            year = (
                tags.get('TDRC').text[0] if 'TDRC' in tags else
                tags.get('TYER').text[0] if 'TYER' in tags else
                'Unknown Year'
            )

            logging.debug(f"Printing year:\n{year}\n")

        elif file_path.suffix == '.flac':
            audio = FLAC(file_path)
            title = audio.get('title', ['Unknown Title'])[0]
            artist = audio.get('artist', ['Unknown Artist'])[0]
            album = audio.get('album', ['Unknown Album'])[0]
            year = audio.get('date', ['Unknown Year'])[0]

        elif file_path.suffix == '.ogg':
            audio = OggVorbis(file_path)
            title = audio.get('title', ['Unknown Title'])[0]
            artist = audio.get('artist', ['Unknown Artist'])[0]
            album = audio.get('album', ['Unknown Album'])[0]
            year = audio.get('date', ['Unknown Year'])[0]

        else:
            raise ValueError("Unsupported file type")

        logging.debug(f"Mutagen audio package\n\n{audio}\n\n")
        metadata = {"title": title, "artist": artist, "album": album, "year": year}
        logging.debug(f"Mutagen metadata\n\n{metadata}\n\n")
        return metadata
    except Exception as e:
        logging.error(f"Failed to retrieve metadata for {file_path}: {e}")
        return {"title": "Unknown Title", "artist": "Unknown Artist", "album": "Unknown Album", "year": "Unknown Year"}

# Get metadata using AcoustID
def get_metadata_from_acoustid(file_path, config):
    try:
        duration, fingerprint = acoustid.fingerprint_file(file_path)
        if not fingerprint or not duration:
            logging.error(f"Fingerprint or duration is invalid for {file_path}")
            return None
    except Exception as e:
        logging.error(f"Error generating fingerprint for {file_path}: {e}")
        return None

    try:
        result = acoustid.lookup(config['acoustid_key'], fingerprint, float(duration))
        logging.debug(f"AcoustID results\n\n{result}\n\n")
        if not result.get('results'):
            logging.error(f"No AcoustID results found for {file_path}")
            return None

        recordings = result['results'][0].get('recordings', [])
        if not recordings:
            logging.error(f"No recordings found in AcoustID results for {file_path}")
            return None

        recording = recordings[0]
        title = recording.get('title', 'Unknown Title')
        artists = recording.get('artists', [])
        artist = artists[0]['name'] if artists else 'Unknown Artist'

        musicbrainz_id = recording.get('id')
        if musicbrainz_id:
            musicbrainz_metadata = fetch_metadata_from_musicbrainz(musicbrainz_id)
        else:
            musicbrainz_metadata = {"album": "Unknown Album", "year": "Unknown Year"}

        logging.debug(f"AcoustID Metadata: Title='{title}', Artist='{artist}'")
        logging.debug(f"MusicBrainz Metadata: Album='{musicbrainz_metadata['album']}', Year='{musicbrainz_metadata['year']}'")

        return {
            "title": title,
            "artist": artist,
            "album": musicbrainz_metadata.get('album'),
            "year": musicbrainz_metadata.get('year'),
        }
    except Exception as e:
        logging.error(f"AcoustID lookup failed for {file_path}: {e}")
        return None

# Write metadata to the file using Mutagen
def write_metadata(file_path, metadata):
    try:
        title = metadata.get('title', 'Unknown Title')
        artist = metadata.get('artist', 'Unknown Artist')
        album = metadata.get('album', 'Unknown Album')
        year = metadata.get('year', 'Unknown Year')

        logging.info(f"Tags to write for {file_path}: Title='{title}', Artist='{artist}', Album='{album}', Year='{year}'")

        if file_path.suffix == '.mp3':
            audio = MP3(file_path, ID3=ID3)
            if not audio.tags:
                audio.add_tags()
            audio.tags['TIT2'] = TIT2(encoding=3, text=title)
            audio.tags['TPE1'] = TPE1(encoding=3, text=artist)
            audio.tags['TALB'] = TALB(encoding=3, text=album)

            try:
                audio.tags['TDRC'] = TDRC(encoding=3, text=year)
                audio.tags['TYER'] = TYER(encoding=3, text=year)
            except Exception as e:
                logging.error(f"Failed to write year metadata: {e}")

            audio.save()

        elif file_path.suffix == '.flac':
            audio = FLAC(file_path)
            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            audio['date'] = year
            audio.save()

        elif file_path.suffix == '.ogg':
            audio = OggVorbis(file_path)
            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            audio['date'] = year
            audio.save()

        logging.info(f"Metadata written to {file_path}")
    except Exception as e:
        logging.error(f"Failed to write metadata to {file_path}: {e}")

# Scan directory for audio files
def scan_directory(directory_path, config):
    directory = Path(directory_path)
    for file_path in directory.rglob('*'):
        if file_path.suffix in ['.mp3', '.flac', '.ogg']:
            logging.info(f"Processing {file_path}")

            # Retrieve existing metadata
            metadata = get_metadata_with_mutagen(file_path)

            # Check if any essential field is missing
            if metadata:
                required_fields = ['title', 'artist', 'album', 'year']
                missing_fields = [field for field in required_fields if metadata.get(field) in (None, 'Unknown Title', 'Unknown Artist', 'Unknown Album', 'Unknown Year')]

                if not missing_fields:
                    logging
