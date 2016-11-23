from __future__ import print_function
import sys

def main():
    dataset_file = sys.argv[1]
    min_support = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    print(dataset_file, min_support, min_conf)


if __name__ == "__main__":
    main()
