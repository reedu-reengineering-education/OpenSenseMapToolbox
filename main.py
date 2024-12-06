from opensensemaptoolbox import OpenSenseMap
import sys
import os

def read_box_ids_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

if __name__ == "__main__":
    OSM = OpenSenseMap.OpenSenseMap()
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <box_id1> <box_id2> ... OR python main.py -f <file_path>")
        sys.exit(1)

    if sys.argv[1] == '-f':
        if len(sys.argv) != 3:
            print("Usage: python main.py -f <file_path>")
            sys.exit(1)
        file_path = sys.argv[2]
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            sys.exit(1)
        box_ids = read_box_ids_from_file(file_path)
    else:
        box_ids = sys.argv[1:]

    for box_id in box_ids:
        OSM.add_box(box_id)
    
    OSM.save_OSM()
