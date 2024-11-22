#!/bin/bash

rm -rf ._*
docker build -t music_tagger .
docker run --rm -p 7681:7681 -v $(pwd):/media/music music_tagger
