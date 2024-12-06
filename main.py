from opensensemaptoolbox import OpenSenseMap
import sys
import os
import argparse

def read_box_ids_from_file(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some IDs.")
    parser.add_argument('--ids', type=str, nargs='*', help='IDs to process (e.g., ABC123DEF456)')
    parser.add_argument('--file', type=str, help='File containing IDs (one per line)')

    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            print(f"File not found: {args.file}")
            sys.exit(1)
        boxIds = read_box_ids_from_file(args.file)
        print("IDs from file:", boxIds)
    if args.ids:
        boxIds = args.ids
        print("IDs from command line:", args.ids)


    OSM = OpenSenseMap.OpenSenseMap()
    OSM.add_box(boxIds)
    OSM.save_OSM()
