from config import get_db
import requests
from models.order import *




#----------HELPERS------------------------
#-----------------HELPERS DB-------------------------

def getSymbols():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM symbols")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def getSymbolsData():
    conn, cursor = get_db()
    cursor.execute("SELECT name, start_price, final_price FROM symbols WHERE active = TRUE")
    rows = cursor.fetchall()
    conn.close()
    return rows

#-----------HELPERS MAIN----------------------



def checkUser(key):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM users WHERE api_key = %s", (key,))
    rows = cursor.fetchall()

    conn.close()

    
    if not rows:
        print("[CONN]: refused")
        print(f"[ERROR]: key {key} not in database")
        return (False, f"key {key} not in database")
    else:
        print("[CONN]: Initialized...")
        return (True, None)

def checkNumbers(price, volume):
    try:
        price = float(price)
        volume = int(volume)
    except (ValueError, TypeError):
        return (False,"Price and volume must be numbers")
    
    if price <= 0 or volume <= 0:
        return (False,"Use positive numbers")
    
    return (True, None)


def checkSymbol(symbol):
    if symbol not in getSymbols():
        return (False, f"{symbol} is not a real symbol")
    return (True, None)


def createErrorMessage(*msg):
    errorMsg = ""
    for i in msg:
        if i:
            errorMsg += i + "; "
    
    return errorMsg


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
    #make it so you cant make transaction with your own orders by adding "AND user_api_key != %s" to the query
    cursor.execute("SELECT * FROM order_book WHERE symbol=%s AND user_api_key != %s ORDER BY price, created_at", (symbol,key))
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



def checkPosition(key,stock):
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM position WHERE userID = %s AND stock = %s", (key, stock))
    row = cursor.fetchall()
    volume = row[1]
    volume = 10
    conn.close()
    return volume



def updatePosition():
    return


def showTradeLog():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM trade_log")
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
    symbol = orderDict["sym"].upper()

    verifUser, msgKey = checkUser(orderDict["key"])
    verifNum, msgNum = checkNumbers(orderDict["price"],orderDict["vol"] )
    verifSym, msgSym = checkSymbol(symbol)


    if verifUser and verifNum and verifSym:
        print("[API-KEY]: Authorized")
        ORDER_BOOK = OrderBook(getInfoTradesOB(orderDict["sym"], orderDict["key"]))
        newOrder = Order(orderDict["side"],symbol,int(orderDict["price"]),int(orderDict["vol"]),orderDict["key"])
        verif, msg = newOrder.checkOrderBalance()
        if verif:
            trades, reste = ORDER_BOOK.matchOrder(newOrder)

            if reste:
                #addOrderDB(reste)
                print("Il en reste")
            result = {
                "reste":  reste.to_dict() if reste else None,
                "trades": [t.to_dict() for t in trades],
                "error": None
            }
            return result
        else:
            return {"reste": None, "trades": None, "error": msg}
    
    
    errMsg = createErrorMessage(msgKey, msgNum, msgSym)
    
    print("[API-KEY]: Refused")
    return {"reste": None, "trades": None, "error": errMsg}
    


#Format {"reste": Order(), "trades": liste[Order,Order,...], "error": "str" (optional), }


