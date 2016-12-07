from __future__ import print_function
import sys
import csv
import sqlite3
from db_utils import AprioriDB

# constants for keys in data
BORO = "BORO"
CUISINE = "CUISINE DESCRIPTION"
VC = "VIOLATION CODE"
VD = "VIOLATION DESCRIPTION"

def build_integrated_dataset(dataset_file_name, outfile_name):
    integrated_data = []
    with open(dataset_file_name, "r") as data_file:
        make_db = True
        db = AprioriDB("test.db", make_db)
        reader = csv.DictReader(data_file)

        for row in reader:
            borough = row[BORO].strip()
            cuisine = row[CUISINE].strip()
            violation_code = row[VC].strip() if row[VC] else "0"
            violation_description = row[VD] if row[VD] else "No violation"

            violation_description = violation_description.decode("utf-8")
            borough_id = db.insert_or_get_from_cache((borough,), make_db, "b")
            cuisine_id = db.insert_or_get_from_cache((cuisine,), make_db, "c")
            violation_id = db.insert_or_get_from_cache((violation_code, violation_description), make_db, "v")
            integrated_row = [borough_id, cuisine_id, violation_id]
            integrated_data.append(integrated_row)

        # after all the data has been added, commit all changes
        db.commit()

    with open(outfile_name, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(integrated_data)

def main():
    dataset_file = sys.argv[1]
    outfile_name = "INTEGRATED-DATASET.csv"
    build_integrated_dataset(dataset_file, outfile_name)

if __name__ == "__main__":
    main()
