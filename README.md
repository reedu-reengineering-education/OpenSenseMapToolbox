# OpensenseMapToolbox

## Capabillities
- download sensor data per box as csv

## Usage
easiest way to find your osm boxId is to go to [openSenseMap](https://opensensemap.org/) and search for your box's name!
### locally
- setup virtualenv
- use pip install to install requirements
- run `python main.py <box_id1> <box_id2>` ... OR `python main.py -f <file_path>` (path to a file with ids row by row)
### Docker
- add openSenseMap boxId to your OSM object in `main.py`
- builld Docker Image
- mount a dir you want to have the downloaded data using the `-v /your/data/dir/:/osmtoolbox/data` flag while running the Docker image

