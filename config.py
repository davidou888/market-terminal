
import os
import mysql.connector

def get_db():   
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "aDmin@terminaL1263"),
        database=os.getenv("DB_NAME", "trading")
    )
    return conn, conn.cursor()
