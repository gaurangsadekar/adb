from __future__ import print_function
import sys
from db_utils import AprioriDB
import itertools

def get_col_name_for_id(i):
    id_type = None
    if 0 < i < 100:
       id_type = "bid"
    elif 100 < i < 200:
        id_type = "cid"
    elif 200 < i < 300:
        id_type = "vid"
    return id_type

def candidate_gen(prev_itemsets):
    size = len(prev_itemsets[0]) + 1
    print("Generating candidates of size", size)
    candidates = [list(s) for s in itertools.combinations(prev_itemsets, 2)]
    # flatten the sets
    candidates = [reduce(lambda x,y: x.union(y), comb) for comb in candidates]
    # filter size of keysets
    candidates = filter(lambda s: len(s) == size, candidates)
    # check for duplicate combinations
    temp = []
    # adds only unique sets to a buffer
    [temp.append(s) for s in candidates if s not in temp]
    candidates = temp
    # remove sets having duplicate columns by filtering the domains of columns
    candidates = [s for s in candidates
                  if len(set(map(lambda elem: get_col_name_for_id(elem), s))) == size]
    # Prune Step: take all combinations of (size - 1) elements
    # from each of the candidates and check if they are in prev_itemsets
    for itemset in candidates:
        one_less_combinations = itertools.combinations(itemset, len(itemset) - 1)
        [candidates.remove(itemset) for smaller in one_less_combinations if set(smaller) not in prev_itemsets]
    return candidates

def apriori(db, min_sup, min_conf):
    print("###### GENERATING LARGE ITEMSETS ######")
    large_itemsets = []
    # get all large itemsets of size 1
    l1 = reduce(lambda acc, s: acc.union(s),
               db.size_one_itemsets(min_sup).values())
    print("Generated " +`len(l1)` + " itemsets of size 1")
    # make individual sets from each element
    # init apriori
    l = [{s} for s in l1]
    # in large itemsets, store the list of sets by size
    large_itemsets += l

    while len(l) > 0 and len(l[0]) < 3:
        # takes the previous freq itemsets and generates new ones
        l = candidate_gen(l)
        # only keep items that meet support
        l = [itemset for itemset in l if db.get_support(itemset) >= min_sup * db.total_baskets]
        if len(l) > 0:
            print("Generated " + `len(l)` + " itemsets of size " + `len(l[0])`)
        large_itemsets += l

    # sort each itemset in lex order
    large_itemsets = [sorted(list(s), reverse = True) for s in large_itemsets]
    # for each itemset, get support for display
    itemsets_support = {}
    for s in large_itemsets:
        itemsets_support[tuple(s)] = db.get_support(s) * 100.0 / db.total_baskets

    outfile_name = "./output.txt"
    pretty_print_itemsets(itemsets_support, db, min_sup, outfile_name)

    assoc_rules_conf_sup = association_rules(db, large_itemsets, itemsets_support, min_conf)
    pretty_print_rules(assoc_rules_conf_sup, min_conf, outfile_name)

def association_rules(db, itemsets, itemsets_support, min_conf):
    print("###### GENERATING ASSOCIATION RULES ######")
    assoc_rules_conf_sup = {}
    for s in itemsets:
        if len(s) > 1:
            lhs = s[:-1]
            rhs = s[-1]
            s_sup = itemsets_support[tuple(s)]
            conf =  s_sup / itemsets_support[tuple(lhs)]
            if conf >= min_conf:
                str_lhs = db.stringify_itemset(lhs)
                str_rhs = db.stringify_itemset([rhs])
                rule_str = str_lhs + " => " + str_rhs
                assoc_rules_conf_sup[rule_str] = (conf, s_sup)

    return assoc_rules_conf_sup

def pretty_print_itemsets(itemsets_support, db, min_sup, outfile_name):
    sorted_itemsets = sorted(itemsets_support.items(), key = lambda tup: tup[1], reverse = True)
    outfile_buf = []
    print("Frequent Itemsets (Min. Support: ", min_sup, ")")
    outfile_buf.append("Frequent Itemsets (Min. Support = " + `min_sup` + "%)")
    print("======================================")
    outfile_buf.append("======================================")

    for itemset, support in sorted_itemsets:
        str_itemset = db.stringify_itemset(itemset)
        # [ Borough: ___, Cuisine: ___, Violation: ___ ], support
        output_line = str_itemset + ", " + `support`
        print(output_line)
        outfile_buf.append(output_line)

    with open(outfile_name, "w") as f:
        f.write("\n".join(outfile_buf))

def pretty_print_rules(assoc_rules_conf_sup, min_conf, outfile_name):
    sorted_assoc_rules = sorted(assoc_rules_conf_sup.items(), key = lambda tup: tup[1][0], reverse = True)
    outfile_buf = []
    with open(outfile_name, "r") as f:
        outfile_buf = [line.strip() for line in f.readlines()]

    print("Association Rules (Min. Confidence: ", min_conf, ")")
    outfile_buf.append("\n")
    outfile_buf.append("Association Rules (Min. Confidence: " + `min_conf` + "%)")
    print("======================================")
    outfile_buf.append("======================================")

    for rule, tup in sorted_assoc_rules:
        conf, sup = tup
        rule_pretty_str = rule + " (Confidence: " + `conf * 100` + "%, Support: " + `sup` + ")"
        print(rule_pretty_str)
        outfile_buf.append(rule_pretty_str)

    with open(outfile_name, "w") as f:
        f.write("\n".join(outfile_buf))

def main():
    integrated_dataset_file = sys.argv[1]
    min_sup = float(sys.argv[2])
    min_conf = float(sys.argv[3])

    db = AprioriDB("./test.db", make_db = False)
    db.insert_baskets(integrated_dataset_file)

    apriori(db, min_sup, min_conf)

if __name__ == "__main__":
    main()
