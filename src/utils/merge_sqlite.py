#!/usr/bin/env python3
"""Merge two SQLite databases with the same schema into one.

Usage:
    python merge_sqlite.py db_base.db db_other.db --out merged.db
    python merge_sqlite.py db_base.db db_other.db

Behavior:
 - The script uses the first DB as base. If --out is provided it copies the base DB to that path
   and writes merged data there. If --inplace is used, the merging is done directly in the first DB.
 - For each table in the other DB, the script INSERTs rows into the target table using only the
   columns common to both tables. INSERT OR IGNORE is used to avoid primary-key conflicts.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
from typing import List, Tuple


def list_tables(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    return [row[0] for row in cur.fetchall()]


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    # Support schema-qualified names like 'src.TableName'
    if "." in table:
        schema, tbl = table.split(".", 1)
        cur = conn.execute(f"PRAGMA {schema}.table_info('{tbl}')")
    else:
        cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]


def merge_databases(target_path: str, other_path: str, inplace: bool = False) -> None:
    # target_path is the DB where data will be inserted
    # other_path is the DB providing rows to insert
    # increase timeout to reduce chance of 'database is locked'
    # isolation_level=None → autocommit mode; we manage transactions manually
    con = sqlite3.connect(target_path, timeout=30, isolation_level=None)
    try:
        con.execute("PRAGMA foreign_keys=OFF;")

        # ATTACH must happen OUTSIDE a transaction to avoid lock on DETACH
        other_abs = os.path.abspath(other_path)
        con.execute("ATTACH DATABASE ? AS src", (other_abs,))

        # list tables in src
        cur = con.execute("SELECT name FROM src.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        src_tables = [r[0] for r in cur.fetchall()]

        con.execute("BEGIN;")
        try:
            for tbl in src_tables:
                tgt_tables = list_tables(con)
                if tbl not in tgt_tables:
                    print(f"Skipping table '{tbl}': not present in target DB")
                    continue

                src_cols = table_columns(con, f"src.{tbl}")
                tgt_cols = table_columns(con, tbl)

                common_cols = [c for c in tgt_cols if c in src_cols]
                if not common_cols:
                    print(f"No common columns for table '{tbl}', skipping.")
                    continue

                cols_sql = ", ".join([f'"{c}"' for c in common_cols])
                sql = f"INSERT OR IGNORE INTO \"{tbl}\" ({cols_sql}) SELECT {cols_sql} FROM src.\"{tbl}\";"
                print(f"Merging table '{tbl}' ({len(common_cols)} cols)")
                con.execute(sql)

            con.execute("COMMIT;")
        except Exception:
            con.execute("ROLLBACK;")
            raise

        # DETACH outside the transaction
        con.execute("DETACH DATABASE src")
    finally:
        con.close()


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Merge two SQLite databases with the same schema")
    p.add_argument("base", help="Base database (will receive rows)")
    p.add_argument("other", help="Other database to merge into base")
    p.add_argument("--out", help="Output path. If omitted a copy of base with suffix _merged.db is used")
    args = p.parse_args(argv)

    base = args.base
    other = args.other

    if not os.path.exists(base):
        print(f"Base DB not found: {base}")
        return 2
    if not os.path.exists(other):
        print(f"Other DB not found: {other}")
        return 2

    if args.out:
        target = args.out
    else:
        root, ext = os.path.splitext(base)
        target = f"{root}_merged{ext or '.db'}"

    # copy base to target
    print(f"Copying base DB {base} -> {target}")
    shutil.copyfile(base, target)

    merge_databases(target, other)
    print("Merge completed.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
