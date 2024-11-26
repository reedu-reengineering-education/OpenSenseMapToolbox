# OpensenseMapToolbox

## Capabillities
- download sensor data per box as csv

## Usage
### locally
setup virtualenv
use pip install to install requirements
add OpensensorMap boxId to your OSM object in `main.py`
### Docker
builld and run Docker Image
mount a dir you want to have the downloaded data in using `-v /your/data/dir/:/osmtoolbox/data` flag
