#!/bin/bash

rm -rf ._*
docker build -t music_tagger .
docker run --rm -v $(pwd):/media/music music_tagger
