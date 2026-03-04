from config import get_db
import requests
from classes import * 


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

#order_book = OrderBook()

#createOrder("B", 104, 10)
#x = Order("S","GOOGL", 100,10,"abc_1234")
#y = Order("B","GOOGL", 95,10,"abc_1234")
#z = Order("B", "GOOGL", 100, 15, "allo1234")
#
#order_book.matchOrder(x)
#order_book.matchOrder(y)
#order_book.matchOrder(z)
#
#OrderBook.print_order_book(order_book)



#482d8efe-5676-45a8-b70e-3f9317ecba66




response = requests.get("http://localhost:8000/post-order?key=key_abc123&side=S&sym=GOOGL&price=10&vol=6542")
#response = requests.get("http://localhost:8000/")
print("STATUS:", response.status_code)
print("Reste:", response.json()["reste"])
i = 0
for l in response.json()["trades"]:
    i += 1
    print(f"trade {i}: {l}")



cursor.execute("SELECT * FROM order_book WHERE side='B'")
rows = cursor.fetchall()

#for row in rows:
#    print("[BUY] prix:", float(row[2]), "volume", row[3])


cursor.execute("SELECT * FROM order_book WHERE side='S'")
rows = cursor.fetchall()
#for row in rows:
#    print("[SELL] prix:", float(row[2]), "volume", row[3])

conn.close()

