import time
from sortedcontainers import SortedDict # pyright: ignore[reportMissingImports]
from collections import deque
import uuid
from extension import socketio
from datetime import datetime

from config import get_db





def addOrderOB(order):
    conn, cursor = get_db()
    cursor.execute("INSERT INTO order_book (id,side,symbol, price, quantity, user_api_key) VALUES (%s,%s, %s, %s, %s, %s)", (order.id,order.side,order.symbol, order.price, order.volume, order.userKey))
    conn.commit()
    conn.close()
    print(f"[DB]: added order ID:{order.id} to order_book" )

def delOrderOB(order):
   conn, cursor = get_db()
   cursor.execute("DELETE FROM order_book WHERE id = %s", (order.id,))
   conn.commit()
   conn.close()
   print(f"[DB]: deleted order ID:{order.id} from order_book" )


def alterOrderOB(order):
   
   print(f"order.vol = {order.volume}")
   conn, cursor = get_db()
   cursor.execute("UPDATE order_book SET quantity= %s WHERE id=%s", (order.volume, order.id))
   conn.commit()
   conn.close()
   print(f"[DB]: updated order ID:{order.id} from order_book to have vol: {order.volume}" )


def getMoneyUser(apiKey):
   conn, cursor = get_db()
   cursor.execute("SELECT balance FROM users WHERE api_key = %s", (apiKey,))
   row = cursor.fetchall()
   conn.close()
   return int(row[0][0])
   

def updateBalance(trade):
   newBalanceSeller = getMoneyUser(trade.sellerApiKey) + (trade.quantity * trade.price)
   newBalanceBuyer = getMoneyUser(trade.buyerApiKey) - (trade.quantity * trade.price)
   print(f"Seller: {newBalanceSeller}")
   print(f"Buyer: {newBalanceBuyer}")
   conn, cursor = get_db()
   cursor.execute("UPDATE users SET balance= %s WHERE api_key=%s", (newBalanceSeller, trade.sellerApiKey))
   conn.commit()
   cursor.execute("UPDATE users SET balance= %s WHERE api_key=%s", (newBalanceBuyer, trade.buyerApiKey))
   conn.commit()
   conn.close()



   





class Order:
   def __init__(self,side, symbol, price, volume, userKey,id = ""):
      if id:
         self.id = id
      else:
         self.id = str(uuid.uuid4())
      self.side = side
      self.symbol = symbol
      self.price = price
      self.volume = volume
      self.userKey = userKey
      self.timestamp = time.time()
   

   def to_dict(self):
      return {
         "id":        self.id,
         "side":      self.side,
         "symbol":    self.symbol,
         "price":     float(self.price),  
         "quantity":  self.volume,
         "timestamp": str(self.timestamp),
      }




   def updateVol(self,tradedVol):
       self.volume -= tradedVol
   
   def checkOrderBalance(self):
      if self.side == "S":
         return (True,"No checks needed")
      
      conn, cursor = get_db()
      cursor.execute("SELECT balance FROM users WHERE api_key = %s", (self.userKey,))
      row = cursor.fetchall()
      if len(row) != 1:
         return (False,"user key invalid")
      else:
         if int(row[0][0]) - (self.price * self.volume)>=0:
            return (True, f"user has {int(row[0][0])}$ and will have {int(row[0][0]) - (self.price * self.volume)}$")
         else:
            return (False, f"INSUF. FUNDS: user has {int(row[0][0])}$ and wants to spend {(self.price * self.volume)}$")
         
      

      conn.close()
      

   def __str__(self):
    return f"[Order]: {self.volume} stocks of {self.symbol} at {self.price} made at {self.timestamp}"


class Trade:
   def __init__(self, buy_order: Order, sell_order: Order, price, quantity):
      self.buy_order_id = buy_order.id
      self.buyerApiKey = buy_order.userKey
      self.sell_order_id = sell_order.id
      self.sellerApiKey = sell_order.userKey
      self.symbol = buy_order.symbol
      self.price = price
      self.quantity = quantity
      self.timestamp = datetime.now()
   

   def to_dict(self):
      return {
         "buy_order_id":  self.buy_order_id,
         "sell_order_id": self.sell_order_id,
         "symbol":        self.symbol,
         "price":         float(self.price),
         "quantity":      self.quantity,
         "timestamp":     str(self.timestamp),
      }

   def logTrade(self):
      conn, cursor = get_db()
      cursor.execute("INSERT INTO trade_log (buy_order_id, sell_order_id, symbol, price, quantity, created_at) VALUES (%s,%s, %s, %s, %s, %s)", (self.buy_order_id,self.sell_order_id, self.symbol,self.price, self.quantity, self.timestamp))
      conn.commit()
      conn.close()
      print(f"[DB]: added trade to trade_log" )

   
   def makeTrade(self):
      self.logTrade()
      updateBalance(self)




class OrderBook:
   def __init__(self, rows):
      # price → deque of orders
      self.asks = SortedDict()
      self.bids = SortedDict(lambda x: -x)

      for row in rows:
         #print("row:", row)
         price = row[3]

         if row[1] == "S":
            if price not in self.asks:
                  self.asks[price] = deque()
            self.asks[price].append(row)
         else:
            if price not in self.bids:
                  self.bids[price] = deque()
            self.bids[price].append(row)


      #print("ASKS:",self.asks) 
      #rint("BID:",self.bids) 
   

   

   def print_order_book(book):
      print("=== BIDS ===")
      for price, queue in book.bids.items():
         for order in queue:
               print(order)

      print("=== ASKS ===")
      for price, queue in book.asks.items():
         for order in queue:
               print(order)
       


   def matchOrder(self,order: Order):
      trades = []
      remainder: Order = order
      opposite = self.bids if order.side == "S" else self.asks

      for price, queue in list(opposite.items()):
         if (order.side == 'B' and order.price < price) or \
            (order.side == 'S' and order.price > price):
            print("[TRADE]: No order found to match")
            break
         
         while queue and remainder.volume > 0 and \
            ((order.side == 'B' and order.price >= price) or \
            (order.side == 'S' and order.price <= price)):
            
            match_order = Order(*queue[0][1:5], queue[0][6], queue[0][0])
            traded_vol = min(remainder.volume, match_order.volume)
            trades.append(Trade(remainder if order.side == "B" else match_order, 
                    match_order if order.side == "B" else remainder,
                    price, traded_vol))
            
            #on envoie un event socket au CLIENT pour dire qu'un trade a eu lieu, avec les infos du trade
            socketio.emit("made_trade", {"symbol": order.symbol, "quantity": float(traded_vol), "price": float(price)})
            print("[TRADE]: Trade happend !")

            remainder.updateVol(traded_vol)
            match_order.updateVol(traded_vol)

            if match_order.volume == 0:
               print("should delete")
               delOrderOB(match_order)
               queue.popleft()
            else:
               print("should alter")
               alterOrderOB(match_order)

         
         if not queue:
            del opposite[price]
         
         if remainder.volume == 0:
            break
      
      if remainder.volume > 0:
         addOrderOB(remainder)
      
      for trade in trades:
         trade.makeTrade()
         

      return trades, remainder if remainder.volume > 0 else None

            
