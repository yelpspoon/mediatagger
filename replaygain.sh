#!/bin/bash

# Enable error handling
set -e

# Check for required tools
command -v vorbisgain >/dev/null 2>&1 || { echo "vorbisgain is required but not installed. Aborting."; exit 1; }
command -v metaflac >/dev/null 2>&1 || { echo "metaflac is required but not installed. Aborting."; exit 1; }
command -v mp3gain >/dev/null 2>&1 || { echo "mp3gain is required but not installed. Aborting."; exit 1; }

# Function to process ogg files
process_ogg() {
    local file="$1"
    echo "Applying ReplayGain to OGG file: $file"
    vorbisgain -a -q "$file"  # Album gain (-a), quiet mode (-q)
}

# Function to process flac files
process_flac() {
    local file="$1"
    echo "Applying ReplayGain to FLAC file: $file"
    metaflac --add-replay-gain "$file"
}

# Function to process mp3 files
process_mp3() {
    local file="$1"
    echo "Applying ReplayGain to MP3 file: $file"
    mp3gain -r -k -q "$file"  # Track gain (-r), avoid clipping (-k), quiet mode (-q)
}

# Recursively find and process files
find . -type f \( -iname "*.ogg" -o -iname "*.flac" -o -iname "*.mp3" \) | while read -r file; do
    extension="${file##*.}"
    case "$extension" in
        ogg)
            process_ogg "$file"
            ;;
        flac)
            process_flac "$file"
            ;;
        mp3)
            process_mp3 "$file"
            ;;
        *)
            echo "Unknown file type: $file"
            ;;
    esac
done

echo "ReplayGain processing completed!"
