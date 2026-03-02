from key import get_db
import requests





#----------HELPERS------------------------

#-----------HELPERS MAIN----------------------

def checkSymbol(symbol):
    return True

def checkUser(key):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM order_book WHERE side='S'")
    rows = cursor.fetchall()


    cursor.execute("SELECT * FROM users WHERE api_key = %s", (key,))
    rows = cursor.fetchall()

    conn.close()

    
    if not rows:
        print("[CONN]: refused")
        print("[ERROR]: key not in database")
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
        cursor.execute("SELECT * FROM order_book")
        rows = cursor.fetchall()
        conn.close()
        result = [lst[1:-1] for lst in rows]
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




def separateOrder(key, side, price, volume):

    if side == "sell":
        createSellOrder()
    else:
        createBuyOrder()
    matchEngine()


def createSellOrder(price, volume):
    conn, cursor = get_db()
    cursor.execute("INSERT INTO order_book (side, price, quantity) VALUES ('S', %s, %s)", ( price, volume))
    conn.commit()
    conn.close()

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

def checkMoney():
    return True

def updatePosition():
    return


def matchEngine():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM order_book WHERE side='B' ORDER BY price DESC, created_at DESC")
    rowsBUY = cursor.fetchall()
    print("RB1",float(rowsBUY[0][2]))

    cursor.execute("SELECT * FROM order_book WHERE side='S' ORDER BY price ASC, created_at DESC")
    rowsSELL = cursor.fetchall()
    print("RS1",float(rowsSELL[0][2]))
    conn.close()
    while(rowsBUY[0][4] >= rowsSELL[0][4]):
        print("[SOLD]", rowsBUY[0][3], "at", float(rowsBUY[0][2]))


#-------------------MAIN FUNCTIONS----------------------

def getTrades(key,symbol=""):
    if checkUser(key) :
        print("[CONN]: retriving trades")
        return getInfoTrades(symbol)
    print("[CONN]: failed")
    return checkUser(key)


def getPositions(key,symbol=""):
    if checkUser(key) :
        print("[CONN]: retriving trades")
        return getInfoPositions(key, symbol)
    print("[CONN]: failed")
    return checkUser(key)


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
