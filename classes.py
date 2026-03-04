import time
from sortedcontainers import SortedDict
from collections import deque
import itertools
import uuid
from datetime import datetime

from key import get_db


_order_counter = itertools.count(1)


def addOrderDB(order):
    conn, cursor = get_db()
    cursor.execute("INSERT INTO order_book (id,side,symbol, price, quantity, user_api_key) VALUES (%s,%s, %s, %s, %s, %s)", (order.id,order.side,order.symbol, order.price, order.volume, order.userKey))
    conn.commit()
    conn.close()
    print(f"[DB]: added order ID:{order.id} to order_book" )

def delOrderDB(order):
   conn, cursor = get_db()
   cursor.execute("DELETE FROM order_book WHERE id = %s", (order.id,))
   conn.commit()
   conn.close()
   print(f"[DB]: deleted order ID:{order.id} from order_book" )


def alterOrderDB(order):
   
   print(f"order.vol = {order.volume}")
   conn, cursor = get_db()
   cursor.execute("UPDATE order_book SET quantity= %s WHERE id=%s", (order.volume, order.id))
   conn.commit()
   conn.close()
   print(f"[DB]: updated order ID:{order.id} from order_book to have vol: {order.volume}" )





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

   def updateVol(self,newVol):
       self.volume = newVol

   def __str__(self):
    return f"[Order]: {self.volume} stocks of {self.symbol} at {self.price} made at {self.timestamp}"


class Trade:
   def __init__(self, buy_order: Order, sell_order: Order, price, quantity):
      self.buy_order_id = buy_order.id
      self.sell_order_id = sell_order.id
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
      cursor.execute("INSERT INTO trade_log (buy_order_id, sell_order_id, symbol, price, quantity, timestamp) VALUES (%s,%s, %s, %s, %s, %s)", (self.buy_order_id,self.sell_order_id, self.symbol,self.price, self.quantity, self.timestamp))
      conn.commit()
      conn.close()
      print(f"[DB]: added trade to trade_log" )



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


      #print(f"remainder id: {remainder.id}")
      opposite = self.bids if order.side == "S" else self.asks

      print(f"Opposite: {opposite}")

      

      #print(f"[DEBUG] order: {order.side} {order.price} vol={getattr(order, 'volume', None) or getattr(order, 'quantity', None)}")
      #print(f"[DEBUG] opposite book: {dict(opposite)}")

      for price, queue in list(opposite.items()):
         if (order.side == 'B' and order.price < price) or \
            (order.side == 'S' and order.price > price):
            print("[TRADE]: No order found to match")
            break
         
         while queue and remainder.volume > 0 and \
            ((order.side == 'B' and order.price >= price) or \
            (order.side == 'S' and order.price <= price)):
            
            match_order = Order(*queue[0][1:5], queue[0][6], queue[0][0])
            #print(f"match order id: {match_order.id}")
            traded_vol = min(remainder.volume, match_order.volume)
            #print("[TRADE]: Trade happend !")
            trades.append(Trade(remainder if order.side == "B" else match_order, 
                    match_order if order.side == "B" else remainder,
                    price, traded_vol))
            print("[TRADE]: Trade happend !")

            remainder.volume -= traded_vol
            match_order.volume -= traded_vol
            if match_order.volume == 0:
               print("should delete")
               delOrderDB(match_order)
               queue.popleft()
            else:
               print("should alter")
               alterOrderDB(match_order)

         
         if not queue:
            del opposite[price]
         
         if remainder.volume == 0:
            break
      
      if remainder.volume > 0:
         addOrderDB(remainder)
      
      for trade in trades:
         trade.logTrade()

      return trades, remainder if remainder.volume > 0 else None

            
