# OpensenseMapToolbox

## Capabillities
- download sensor data per box as csv

## Usage
easiest way to find your osm boxId is to go to [openSenseMap](https://opensensemap.org/) and search for your box's name!
### locally
- setup virtualenv
- use pip install to install requirements
- add openSenseMap boxId to your OSM object in `main.py`
- run `main.py`
### Docker
- add openSenseMap boxId to your OSM object in `main.py`
- builld Docker Image
- mount a dir you want to have the downloaded data using the `-v /your/data/dir/:/osmtoolbox/data` flag while running the Docker image

