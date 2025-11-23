from fastapi import APIRouter, Query
from typing import Optional
import mysql.connector
import os

router = APIRouter(prefix="/helmsman", tags=["helmsman"])

def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "cockswain-mysql"),
        user=os.getenv("MYSQL_USER", "cockswain_core"),
        password=os.getenv("MYSQL_PASSWORD", "changeme"),
        database=os.getenv("MYSQL_DATABASE", "cockswain"),
    )

@router.get("/list-all")
def list_all(
    q: Optional[str] = Query(None, description="關鍵字"),
    source: Optional[str] = Query(None, description="資料來源過濾 chatgpt/manual/ext_ai/system")
):
    db = get_db()
    cur = db.cursor(dictionary=True)

    resp = {
        "inbox_docs": [],
        "tasks": [],
        "nodes": []
    }

    # inbox_docs
    sql = "SELECT id, filename, path, source, created_at FROM inbox_docs WHERE 1=1"
    params = []
    if q:
        sql += " AND (filename LIKE %s OR path LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    if source:
        sql += " AND source = %s"
        params.append(source)
    cur.execute(sql, params)
    resp["inbox_docs"] = cur.fetchall()

    # tasks
    sql = "SELECT id, title, status, source, created_at FROM tasks WHERE 1=1"
    params = []
    if q:
        sql += " AND title LIKE %s"
        params.append(f"%{q}%")
    if source:
        sql += " AND source = %s"
        params.append(source)
    cur.execute(sql, params)
    resp["tasks"] = cur.fetchall()

    # nodes
    sql = "SELECT id, node_name, ip_addr, status, source, last_seen FROM nodes"
    cur.execute(sql)
    resp["nodes"] = cur.fetchall()

    cur.close()
    db.close()
    return resp


from fastapi import APIRouter, Query
from typing import Optional
import mysql.connector
import os

router = APIRouter(prefix="/helmsman", tags=["helmsman"])

def get_db():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "cockswain-mysql"),
        user=os.getenv("MYSQL_USER", "cockswain_core"),
        password=os.getenv("MYSQL_PASSWORD", "changeme"),
        database=os.getenv("MYSQL_DATABASE", "cockswain"),
    )

@router.get("/list-all")
def list_all(
    q: Optional[str] = Query(None, description="關鍵字"),
    source: Optional[str] = Query(None, description="資料來源過濾 chatgpt/manual/ext_ai/system")
):
    db = get_db()
    cur = db.cursor(dictionary=True)

    resp = {
        "inbox_docs": [],
        "tasks": [],
        "nodes": []
    }

    # inbox_docs
    sql = "SELECT id, filename, path, source, created_at FROM inbox_docs WHERE 1=1"
    params = []
    if q:
        sql += " AND (filename LIKE %s OR path LIKE %s)"
        params += [f"%{q}%", f"%{q}%"]
    if source:
        sql += " AND source = %s"
        params.append(source)
    cur.execute(sql, params)
    resp["inbox_docs"] = cur.fetchall()

    # tasks
    sql = "SELECT id, title, status, source, created_at FROM tasks WHERE 1=1"
    params = []
    if q:
        sql += " AND title LIKE %s"
        params.append(f"%{q}%")
    if source:
        sql += " AND source = %s"
        params.append(source)
    cur.execute(sql, params)
    resp["tasks"] = cur.fetchall()

    # nodes
    sql = "SELECT id, node_name, ip_addr, status, source, last_seen FROM nodes"
    cur.execute(sql)
    resp["nodes"] = cur.fetchall()

    cur.close()
    db.close()
    return resp
