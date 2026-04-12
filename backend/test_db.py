import psycopg2
from psycopg2.extras import RealDictCursor
import re

class DBWrapper:
    def __init__(self, conn):
        self.conn = conn
        
    def execute(self, query, params=None):
        q = query.replace('?', '%s')
        
        # Super hacky way to support lastrowid:
        is_insert = q.strip().upper().startswith("INSERT INTO")
        if is_insert and "RETURNING " not in q.upper():
            q += " RETURNING id"
            
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        if params:
            cursor.execute(q, params)
        else:
            cursor.execute(q)
            
        if is_insert:
            try:
                row = cursor.fetchone()
                if row and 'id' in row:
                    cursor.lastrowid = row['id']
            except Exception as e:
                pass
                
        return cursor
        
    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    print("Syntax ok!")
