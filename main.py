# from OpenSenseMap import OpenSenseMap
# from Box import Box
# from Sensor import Sensor

from opensensemaptoolbox import OpenSenseMap
from opensensemaptoolbox import Box
import pandas as pd



OSM = OpenSenseMap.OpenSenseMap()

# all_boxes = OSM.get_data('https://api.opensensemap.org/boxes')
boxids = pd.read_csv("./boxIDs.csv")
res= [b for b in boxids['id']]
# res = []
# for i, box in enumerate(all_boxes):
#     sens = box['sensors']
#     print(i)
#     for sen in sens:
#         if 'title' in sen.keys():
#             if sen['title'] == "Surface Sett":
#                 res.append(box['_id'])
# df = pd.DataFrame(dict(id=res))
# df.to_csv('./boxIDs.csv')
for box in res:
    print(f'XXXXXXXXXXXXXXXXXXXXXXXXX    {box}    XXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
    OSM.add_box(box)
OSM.save_OSM()


