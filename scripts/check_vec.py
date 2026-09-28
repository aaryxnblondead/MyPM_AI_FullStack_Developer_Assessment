"""Smoke test sqlite-vec extension loading and vec0 queries."""
import sqlite3
import sys


def main() -> None:
    try:
        import sqlite_vec
    except Exception as e:
        print(f"FAIL: could not import sqlite-vec: {e}")
        print("Fix: install with backend venv python -m pip install -r backend/requirements.txt")
        sys.exit(1)
    try:
        con = sqlite3.connect(":memory:")
        con.enable_load_extension(True)
    except Exception as e:
        print(f"FAIL: SQLite extension loading is disabled in this Python build: {e}")
        print("Fix: use python.org Python or uv Python, not a build with SQLITE_OMIT_LOAD_EXTENSION.")
        sys.exit(1)
    try:
        con.load_extension(sqlite_vec.loadable_path())
    except Exception as e:
        print(f"FAIL: could not load sqlite-vec extension: {e}")
        print(f"Fix: check sqlite_vec path {sqlite_vec.loadable_path()} matches OS and arch.")
        sys.exit(1)
    version = con.execute("select vec_version()").fetchone()[0]
    con.execute("CREATE VIRTUAL TABLE v USING vec0(embedding FLOAT[4] distance_metric=cosine)")
    con.execute("INSERT INTO v(rowid, embedding) VALUES (1, '[1,0,0,0]'), (2, '[0,1,0,0]')")
    rows = con.execute(
        "SELECT rowid, distance FROM v WHERE embedding MATCH '[1,0,0,0]' ORDER BY distance LIMIT 2"
    ).fetchall()
    assert rows[0][0] == 1, f"expected row 1 first, got {rows}"
    print(f"vec_version={version} rows={rows} ok")


if __name__ == "__main__":
    main()
