# mediatagger
Unraid app to fill in basic metadata missing from Ogg, Flac and MP3 files.
This is the basis for an UnRaid Docker app.

### Usage
The front-end via Unraid's Docker apps will open to a `ttyd` terminal.
The container will have /mnt/user/media attached to the container as /media/music
There will be a MOTD that displays command usage.

### Config
For Unraid, point it at your Audio/Media directory to save output.

#### Unraid
- Docker -> Add Container
  - Template from `chatai` and adjust port(s) and volume mounts as needed
  - Have an image in /mnt/user/Media/pictures/avatars/icon_<name>.png
  - `ttyd` will need a port mapped to an unused port on the Unraid host
  - Add ENV vars in the template for the following:
    - ACOUSTID_KEY="<API_KEY>"
    - ACOUSTID_NAME="metascan"
    - ACOUSTID_VERSION="v.01"
    - SCAN_DIRECTORY="/media/music"

#### Github
- Credentials for DockerHub
  - <repo>/settings/secrets/actions
    - DOCKER_USERNAME
    - DOCKER_PASSWORD
- setup GH Actions using the `docker-image.yml` template

### Requirements
Unraid.  But this Python file can be used via CLI with few changes.
Github to store the container image (built with Github Actions).


### References
- https://selfhosters.net/docker/templating/templating/
- https://github.com/binhex/docker-templates


