from config import get_db
import requests


conn, cursor = get_db()





def matchEngine():
    cursor.execute("SELECT * FROM order_book WHERE side='B' ORDER BY price DESC, created_at DESC")
    rowsBUY = cursor.fetchall()
    print("RB1",float(rowsBUY[0][2]))

    cursor.execute("SELECT * FROM order_book WHERE side='S' ORDER BY price ASC, created_at DESC")
    rowsSELL = cursor.fetchall()
    print("RS1",float(rowsSELL[0][2]))

    while(rowsBUY[0][2] >= rowsSELL[0][2]):
        print("[SOLD]", rowsBUY[0][3], "at", float(rowsBUY[0][2]))



#createOrder("B", 104, 10)






response = requests.get("http://localhost:8000/get-pos?key=key_abc123")
print("STATUS:", response.status_code)
print("TEXT:", response.text)



cursor.execute("SELECT * FROM order_book WHERE side='B'")
rows = cursor.fetchall()

#for row in rows:
#    print("[BUY] prix:", float(row[2]), "volume", row[3])


cursor.execute("SELECT * FROM order_book WHERE side='S'")
rows = cursor.fetchall()
#for row in rows:
#    print("[SELL] prix:", float(row[2]), "volume", row[3])

conn.close()

