# from OpenSenseMap import OpenSenseMap
# from Box import Box
# from Sensor import Sensor

from opensensemaptoolbox.OpenSenseMap import OpenSenseMap
from opensensemaptoolbox.Box import Box
from opensensemaptoolbox.Sensor import Sensor
import pandas as pd



OSM = OpenSenseMap()
# bs = OSM.box_sensor_dict_by_tag(tag='ATRAI')
df_ids = OSM.read_csv('./bikeBoxIds.csv')
OSM.add_box([x for x in df_ids['bikeBoxId']])
OSM.save_OSM()
OSM.add_box('66bccabdee77e400087c454a')
ss = Sensor('66bccabdee77e400087c454a')
a = 1