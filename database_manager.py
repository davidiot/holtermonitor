import sqlite3 as sql3


def upload(time, ecg, pvcs):
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS ecg_data")
    c.execute("CREATE TABLE ecg_data (IND INTEGER, TIME REAL, ECG REAL)")

    c.execute("DROP TABLE IF EXISTS metadata")
    c.execute("CREATE TABLE metadata (LENGTH INTEGER)")
    c.execute("INSERT INTO metadata (LENGTH) VALUES(?)", [len(ecg)])

    c.execute("DROP TABLE IF EXISTS pvc_data")
    c.execute("CREATE TABLE pvc_data (IND INTEGER, CERTAINTY INTEGER)")

    for i, (t, e) in enumerate(zip(time, ecg)):
        c.execute(
            "INSERT INTO ecg_data (IND, TIME, ECG) VALUES(?, ?, ?)",
            (i, float(t), float(e))
        )

    for (ind, certainty) in pvcs:
        c.execute(
            "INSERT INTO pvc_data (IND, CERTAINTY) VALUES(?, ?)",
            (int(ind), int(certainty))
        )

    conn.commit()
    conn.close()


def query_length():
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()
    result = c.execute("SELECT LENGTH FROM metadata").fetchone()[0]
    c.close()
    return result


def query_pvcs():
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()
    result = c.execute("SELECT IND, CERTAINTY FROM pvc_data").fetchall()
    c.close()
    return [[i, c] for (i, c) in result]


def query_data(start, end):
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()
    result = c.execute("""
              SELECT TIME, ECG FROM ecg_data
              WHERE TIME >= ? and TIME < ?
              ORDER BY TIME
              """, [start, end]).fetchall()
    time, ecg = zip(*result)
    c.close()
    return time, ecg


def query_point(point):
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()
    result = c.execute("""
              SELECT TIME, ECG FROM ecg_data
              WHERE IND = ?
              ORDER BY TIME
              """, [int(point)]).fetchone()
    c.close()
    return result
