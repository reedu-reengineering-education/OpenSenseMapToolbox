# from OpenSenseMap import OpenSenseMap
# from Box import Box
# from Sensor import Sensor
import os
from opensensemaptoolbox import utils
from opensensemaptoolbox import OpenSenseMap
from opensensemaptoolbox import Box
import pandas as pd



if __name__ == "__main__":
    OSM = OpenSenseMap.OpenSenseMap()

    #load boxIds
    boxids = pd.read_csv("./boxIDs.csv")
    res= [b for b in boxids['id']]
    #add boxes
    OSM.add_box(res)
    # #OSM.save_OSM()



    b_p = "./data"
    dirs = os.listdir(b_p)

    for dir in dirs:
        data = pd.read_csv(os.path.join(dir, 'data.csv'))
        d_tours = utils.create_tours(data)
        tours = utils.extract_tours(d_tours)
        tours.to_file(os.path.join(dir, f'tours_{os.path.basename(dir)}.geojson'))


