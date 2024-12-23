#!/bin/bash

# Check for required tools
command -v vorbisgain >/dev/null 2>&1 || { echo "vorbisgain is required but not installed. Aborting."; exit 1; }
command -v metaflac >/dev/null 2>&1 || { echo "metaflac is required but not installed. Aborting."; exit 1; }
command -v mp3gain >/dev/null 2>&1 || { echo "mp3gain is required but not installed. Aborting."; exit 1; }

# Log file for errors
LOG_FILE="replaygain_errors.log"

# Clear the log file at the start of execution
> "$LOG_FILE"

# Trap function to handle errors
trap_error() {
    echo "Error processing file: $1" | tee -a "$LOG_FILE"
}

# Function to process ogg files
process_ogg() {
    local file="$1"
    echo "Applying ReplayGain to OGG file: $file"
    if ! vorbisgain -a -q "$file" 2>>"$LOG_FILE"; then
        trap_error "$file"
    fi
}

# Function to process flac files
process_flac() {
    local file="$1"
    echo "Applying ReplayGain to FLAC file: $file"
    if ! metaflac --add-replay-gain "$file" 2>>"$LOG_FILE"; then
        trap_error "$file"
    fi
}

# Function to process mp3 files
process_mp3() {
    local file="$1"
    echo "Applying ReplayGain to MP3 file: $file"
    if ! mp3gain -r -k -q "$file" 2>>"$LOG_FILE"; then
        trap_error "$file"
    fi
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
            echo "Unknown file type: $file" | tee -a "$LOG_FILE"
            ;;
    esac
done

echo "ReplayGain processing completed!"
echo "Errors, if any, have been logged to $LOG_FILE."
