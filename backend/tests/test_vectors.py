import sqlite3

import sqlite_vec


def make_db():
    con = sqlite3.connect(":memory:")
    con.enable_load_extension(True)
    con.load_extension(sqlite_vec.loadable_path())
    con.execute("CREATE VIRTUAL TABLE v USING vec0(chunk_id TEXT, embedding FLOAT[4] distance_metric=cosine)")
    return con


def test_vec_insert_and_nearest():
    con = make_db()
    con.execute("INSERT INTO v(chunk_id, embedding) VALUES ('a', '[1,0,0,0]'), ('b', '[0,1,0,0]')")
    rows = con.execute(
        "SELECT chunk_id, distance FROM v WHERE embedding MATCH '[1,0,0,0]' ORDER BY distance LIMIT 2"
    ).fetchall()
    assert rows[0][0] == "a"
    assert rows[0][1] < rows[1][1]
