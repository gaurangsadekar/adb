import sqlite3
import csv
import collections

class AprioriDB:

    # table name constants
    BOROUGHS = "boroughs"
    CUISINES = "cuisines"
    VIOLATIONS = "violations"
    BASKETS = "baskets"

    # type constants
    cols = ["b", "c", "v"]
    tbls = ["boroughs", "cuisines", "violations"]

    def __init__(self, db_file, make_db = False):
        self.conn = sqlite3.connect(db_file)
        self.conn.text_factory = str
        self.c = self.conn.cursor()

        # all caches are name -> id
        self.borough_cache = {}
        self.cuisine_cache = {}
        self.violation_cache = {}

        # create the mapping tables if make_db is True,
        # create the additional baskets.sql table when it is false
        # this ensure new table creation on every run
        schema_file = "schema.sql" if make_db else "baskets.sql"
        with open(schema_file, "r") as schema:
            sql_script = schema.read()
            self.c.executescript(sql_script)
            self.conn.commit()

    ## cache fns
    def get_cache_by_type(self, cache_type):
        cache_to_check = None
        if cache_type == "b":
            cache_to_check = self.borough_cache
        elif cache_type == "c":
            cache_to_check = self.cuisine_cache
        elif cache_type == "v":
            cache_to_check = self.violation_cache
        return cache_to_check

    def in_cache(self, elem, cache_type):
        cache = self.get_cache_by_type(cache_type)
        return elem in cache

    def get_from_cache(self, key, cache_type):
       cache = self.get_cache_by_type(cache_type)
       return cache[key]

    def update_cache(self, key, val, cache_type):
        cache = self.get_cache_by_type(cache_type)
        cache[key] = val

    def update_cache_after_insert(self, field_name, cache_type):
        get_fn = self.get_fn_by_type(cache_type)
        rid = get_fn(field_name)
        self.update_cache(field_name, rid, cache_type)
        return rid

    # functions by type
    def get_fn_by_type(self, cache_type):
        get_fn = None
        if cache_type == "b":
            get_fn = self.get_borough_id
        elif cache_type == "c":
            get_fn = self.get_cuisine_id
        elif cache_type == "v":
            get_fn = self.get_violation_id
        return get_fn

    def insert_fn_by_type(self, cache_type):
        insert_fn = None
        if cache_type == "b":
            insert_fn = self.insert_borough
        elif cache_type == "c":
            insert_fn = self.insert_cuisine
        elif cache_type == "v":
            insert_fn = self.insert_violation
        return insert_fn

    ## insert fns
    # borough tup is now (zipcode, borough_name)
    def insert_borough(self, borough_tup):
        print("Inserting borough", borough_tup)
        stmt = "INSERT INTO boroughs (name) VALUES (?)"
        self.c.execute(stmt, borough_tup)
        bid = self.update_cache_after_insert(borough_tup[0], "b")
        return bid

    def insert_cuisine(self, cuisine_tup):
        print("Inserting cuisine", cuisine_tup[0])
        stmt = "INSERT INTO cuisines (name) VALUES (?)"
        self.c.execute(stmt, cuisine_tup)
        cid = self.update_cache_after_insert(cuisine_tup[0], "c")
        return cid

    def insert_violation(self, violation_tup):
        print("Inserting violation", violation_tup)
        stmt = "INSERT INTO violations (code, description) VALUES (?, ?)"
        self.c.execute(stmt, violation_tup)
        violation_code, violation_desc = violation_tup
        vid = self.update_cache_after_insert(violation_code, "v")
        return vid

    def insert_or_get_from_cache(self, field_value_tup, cached, cache_type):
        get_fn = self.get_fn_by_type(cache_type)
        insert_fn = self.insert_fn_by_type(cache_type)
        col = field_value_tup[0]
        ret_id = None
        if self.in_cache(col, cache_type):
            ret_id = get_fn(col, cached)
        else:
            ret_id = insert_fn(field_value_tup)
        return ret_id

    ## get ID fns
    def get_id_col_name(self, cache_type):
        col_name = None
        if cache_type == "b":
            col_name = "name"
        elif cache_type == "c":
            col_name = "name"
        elif cache_type == "v":
            col_name = "code"
        return col_name

    def get_id_from_table(self, table_name, field_value, cached, cache_type):
        ret_id = None
        if not cached:
            col_name = self.get_id_col_name(cache_type)
            stmt = "SELECT id FROM " + table_name  + " WHERE " + col_name  + " = ?"
            self.c.execute(stmt, (field_value,))
            ret_id = self.c.fetchone()[0]
        else:
            ret_id = self.get_from_cache(field_value, cache_type)
        return ret_id

    def get_borough_id(self, zipcode, cached = False):
        return self.get_id_from_table("boroughs", zipcode, cached, "b")

    def get_cuisine_id(self, cuisine, cached = False):
        return self.get_id_from_table("cuisines", cuisine, cached, "c")

    def get_violation_id(self, violation_code, cached = False):
        return self.get_id_from_table("violations", violation_code, cached, "v")

    def commit(self):
        self.conn.commit()

    def insert_baskets(self, integrated_dataset_file_name):
        # list of tuples of baskets
        data = []
        with open(integrated_dataset_file_name, "r") as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                data.append(tuple([int(r) for r in row]))

        self.total_baskets = len(data)
        self.c.executemany("INSERT INTO baskets (bid, cid, vid) VALUES (?, ?, ?)", data)
        self.commit()

    # association rules db functions
    def get_all_ids(self, table_type):
        table_name = None
        if table_type == "b":
            table_name = AprioriDB.BOROUGHS
        elif table_type == "c":
            table_name = AprioriDB.CUISINES
        elif table_type == "v":
            table_name = AprioriDB.VIOLATIONS

        stmt = "select id from " + table_name
        self.c.execute(stmt)
        return self.c.fetchall()

    def size_one_itemsets(self, min_sup_frac):
        min_sup = min_sup_frac * self.total_baskets
        itemsets = collections.defaultdict(set)
        for tt in AprioriDB.cols:
            col_name = tt + "id"
            ids = self.get_all_ids(tt)[1:]
            for i in ids:
                stmt = "select count(*) from baskets where " + col_name + "  = (?)"
                self.c.execute(stmt, (i[0],))
                support = self.c.fetchone()[0]
                if support >= min_sup:
                    itemsets[col_name].add(i[0])
        return itemsets

    def get_support(self, itemset):
        col_names = [AprioriDB.cols[i / 100] for i in itemset]
        stmt = "SELECT COUNT(*) FROM baskets WHERE "
        where = " AND ".join([col + "id=" + `i` for col, i in zip(col_names, itemset)])
        self.c.execute(stmt + where)
        item_sup = self.c.fetchone()[0]
        return item_sup

    def stringify_itemset(self, itemset):
        tbl_names = [AprioriDB.tbls[i / 100] for i in itemset]
        itemset_str = []
        for tbl, i in zip(tbl_names, itemset):
            col = None
            if tbl == AprioriDB.BOROUGHS or tbl == AprioriDB.CUISINES:
                col = "name"
            elif tbl == AprioriDB.VIOLATIONS:
                col = "description"
            stmt = "SELECT " + col + " FROM " + tbl + " WHERE id = (?)"
            self.c.execute(stmt, (i,))
            itemset_str.append(tbl[:-1] + ": " + self.c.fetchone()[0])

        return "[" + ",".join(itemset_str) + "]"

if __name__ == "__main__":
    pass
