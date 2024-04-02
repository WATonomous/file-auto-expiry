from utils import *
import sys


def main(base_folder):
    file_info = collect_expired_file_information(base_folder, 0)
    creator_info = collect_creator_information(file_info)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        
        print("Usage: python file_expiry.py <folder to scan> <temp>")
        sys.exit(1)

    base_folder = sys.argv[1]
    temp_folder = sys.argv[2]

    main(base_folder=base_folder)