from config import get_db
import requests
from models.order import *





#----------HELPERS------------------------

#-----------HELPERS MAIN----------------------

def checkSymbol(symbol):
    return True

def checkUser(key):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM users WHERE api_key = %s", (key,))
    rows = cursor.fetchall()

    conn.close()

    
    if not rows:
        print("[CONN]: refused")
        print(f"[ERROR]: key {key} not in database")
        return ValueError("Invalid API key")
    else:
        print("[CONN]: Initialized...")
        return True


#----------HELPERS TRADES-----------------------


def getInfoTrades(symbol=""):
    if symbol:
        print("[SQL]: get order_book with symbol:", symbol)
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM order_book WHERE symbol=%s", (symbol,))
        rows = cursor.fetchall()
        conn.close()

        result = [lst[1:-1] for lst in rows]
        if result:
            print("[SQL]: succes, returning", len(result), "rows")
        return result
    else:
        print("[SQL]: get all order_book")
        conn, cursor = get_db()
        cursor.execute("SELECT * FROM order_book ORDER BY price, created_at")
        rows = cursor.fetchall()
        conn.close()
        result = [lst[1:-1] for lst in rows]
        if result:
            print("[SQL]: succes, returning", len(result), "rows")
        return result
    
def getInfoTradesOB(symbol, key):
    print("[SQL]: get order_book with symbol:", symbol)
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM order_book WHERE symbol=%s AND user_api_key != %s", (symbol,key))
    rows = cursor.fetchall()
    conn.close()
    result = [lst for lst in rows]
    if result:
        print("[SQL]: succes, returning", len(result), "rows")
    return result

#--------------HELPERS POSITIONS-------------------------------

def getInfoPositions(key, symbol=""):
    conn, cursor = get_db()
    if symbol:
        print("[SQL]: get position with symbol:", symbol)
        cursor.execute("SELECT * FROM positions WHERE symbol=%s AND  user_api_key=%s", (symbol,key))
    else:
        print("[SQL]: get all positions")
        cursor.execute("SELECT * FROM positions WHERE user_api_key=%s", (key,))
    
    rows = cursor.fetchall()
    conn.close()
    result = [lst[2:] for lst in rows]
    if result:
        print("[SQL]: succes, returning", len(result), "rows")
    return result



#-----------------HELPERS ORDER--------------------










def addTradeLog(trade):
    return

def createBuyOrder(price, volume):
    conn, cursor = get_db()
    cursor.execute("INSERT INTO order_book (side, price, quantity) VALUES ('B', %s, %s)", ( price, volume))
    conn.commit()
    conn.close()


def checkPosition(key,stock):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM position WHERE userID = %s AND stock = %s", (key, stock))
    row = cursor.fetchall()
    volume = row[1]
    volume = 10
    conn.close()
    return volume

def checkMoney(key):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM position WHERE userID = %s AND stock = %s", (key, stock))
    row = cursor.fetchall()
    return True

def updatePosition():
    return


def showTradeLog():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM tarde_log")
    rows = cursor.fetchall()
    for row in rows:
        print(row)



#-------------------MAIN FUNCTIONS----------------------





def getTrades(key,symbol=""):
    if checkUser(key) :
        print("[CONN]: retriving trades")
        return getInfoTrades(symbol)
    print("[CONN]: failed")
    return checkUser(key)


def getPositions(key,symbol=""):
    if checkUser(key):
        print("[CONN]: retriving trades")
        return getInfoPositions(key, symbol)
    print("[CONN]: failed")
    return checkUser(key)

def createOrder(orderDict):
    
    if checkUser(orderDict["key"]):
        print("[API-KEY]: Authorized")
        ORDER_BOOK = OrderBook(getInfoTradesOB(orderDict["sym"], orderDict["key"]))
        newOrder = Order(orderDict["side"],orderDict["sym"],int(orderDict["price"]),int(orderDict["vol"]),orderDict["key"])
        verif, msg = newOrder.checkOrderBalance()
        if verif:
            trades, reste = ORDER_BOOK.matchOrder(newOrder)

            if reste:
                #addOrderDB(reste)
                print("Il en reste")
            result = {
                "trades": [t.to_dict() for t in trades],
                "reste":  reste.to_dict() if reste else None
            }
            return result
        else:
            print("[BALANCE]:", msg)
    print("[API-KEY]: Refused")
    return {"reste":f"key: {orderDict["key"]} not in db", "trades": "None"}
    



#createOrder("B", 104, 10)






#conn, cursor = get_db()
#
#
#cursor.execute("SELECT * FROM order_book WHERE side='B'")
#rows = cursor.fetchall()
#
##for row in rows:
##    print("[BUY] prix:", float(row[2]), "volume", row[3])
#
#
#cursor.execute("SELECT * FROM order_book WHERE side='S'")
#rows = cursor.fetchall()
##for row in rows:
##    print("[SELL] prix:", float(row[2]), "volume", row[3])

#conn.close()
