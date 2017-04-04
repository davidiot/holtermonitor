import sqlite3 as sql3


def upload(time, ecg):
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS ecg_data")
    c.execute("CREATE TABLE ecg_data (IND INTEGER, TIME REAL, ECG REAL)")

    c.execute("DROP TABLE IF EXISTS metadata")
    c.execute("CREATE TABLE metadata (LENGTH INTEGER)")
    c.execute("INSERT INTO metadata (LENGTH) VALUES(?)", [len(ecg)])

    for i, (t, e) in enumerate(zip(time, ecg)):
        c.execute(
            "INSERT INTO ecg_data (IND, TIME, ECG) VALUES(?, ?, ?)",
            (i, float(t), float(e))
        )

    conn.commit()
    conn.close()


def query_length():
    conn = sql3.connect('hmdata.db')
    c = conn.cursor()
    result = c.execute("SELECT LENGTH FROM metadata").fetchone()[0]
    c.close()
    return result


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
              """, [point]).fetchone()
    c.close()
    return result
