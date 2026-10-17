#!/usr/bin/env python3
"""Compare SQL execution rate and exact-result accuracy across prompts.

Example:
python metric_comparison.py --labels restaurants_dataset.csv --schema restaurants-schema.csv --database restaurants-db.txt --prediction CLEAR=clear.csv --prediction RACE=race.csv --prediction CRISP=crisp.csv
"""
import argparse, csv, json, re, sqlite3
from collections import Counter

def read_csv(path):
    csv.field_size_limit(1_000_000_000)
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def load_db(schema_path, db_path):
    tables = {}
    with open(schema_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f, skipinitialspace=True):
            if len(row) < 5: continue
            table, field, pk, _fk, raw_type = row[:5]
            table, field = table.strip(), field.strip()
            if table == "-" or table.lower() == "table name": continue
            t = raw_type.strip().lower()
            typ = "INTEGER" if t.startswith("int") else "REAL" if t.startswith(("decimal", "float")) else "TEXT"
            tables.setdefault(table, []).append((field, typ, pk.strip().lower() == "y"))
    con = sqlite3.connect(":memory:")
    for table, cols in tables.items():
        defs = ", ".join('"%s" %s%s' % (n, t, " PRIMARY KEY" if pk else "") for n,t,pk in cols)
        con.execute(f'CREATE TABLE "{table}" ({defs})')
    with open(db_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            m = re.fullmatch(r"([A-Z_]+)\((.*)\)", line.rstrip("\r\n"))
            if not m: raise ValueError(f"Invalid database record on line {lineno}")
            table, values = m.groups()
            vals = next(csv.reader([values], skipinitialspace=True))
            if table not in tables or len(vals) != len(tables[table]):
                raise ValueError(f"Unknown table or wrong field count on line {lineno}")
            vals = [int(v) if typ == "INTEGER" else float(v) if typ == "REAL" else v
                    for v, (_, typ, _) in zip(vals, tables[table])]
            con.execute(f'INSERT INTO "{table}" VALUES ({", ".join("?" for _ in vals)})', vals)
    return con

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--labels", required=True); p.add_argument("--schema", required=True); p.add_argument("--database", required=True)
    p.add_argument("--prediction", action="append", required=True, metavar="NAME=CSV", help="Repeat for each prompt")
    a = p.parse_args()
    labels = read_csv(a.labels)
    if not labels: raise ValueError("No labels found")
    refs = {r["question"]: json.loads(r["result"]) for r in labels}
    con = load_db(a.schema, a.database)
    print("prompt,questions,sql_executable,execution_rate,exact_correct,exact_accuracy,sql_errors")
    for spec in a.prediction:
        name, path = spec.split("=", 1); rows = read_csv(path)
        if len(rows) != len(labels): raise ValueError(f"{name}: {len(rows)} predictions, expected {len(labels)}")
        if [r["question"] for r in rows] != [r["question"] for r in labels]:
            raise ValueError(f"{name}: questions differ or are out of order")
        executable = correct = errors = 0
        for row in rows:
            try:
                got = con.execute(row["predicted_sql"]).fetchall(); executable += 1
                correct += Counter(map(tuple, got)) == Counter(map(tuple, refs[row["question"]]))
            except sqlite3.Error:
                errors += 1
        n = len(rows)
        print(f"{name},{n},{executable},{executable/n:.6f},{correct},{correct/n:.6f},{errors}")
    con.close()

if __name__ == "__main__": main()
