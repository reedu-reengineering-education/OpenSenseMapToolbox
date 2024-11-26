from opensensemaptoolbox import OpenSenseMap


if __name__ == "__main__":
    OSM = OpenSenseMap.OpenSenseMap()
    #add boxes
    OSM.add_box('123456789ABCDEF')
    #saves data
    OSM.save_OSM()


