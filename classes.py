import time
from sortedcontainers import SortedDict
from collections import deque


class InfoRequest:
     def __init__(self, key: str, symbol=""):
        self.key = key
        self.symbol = symbol


class Order:
   def __init__(self,side, symbol, price, volume, userKey):
      self.side = side
      self.symbol = symbol
      self.price = price
      self.volume = volume
      self.userKey = userKey
      self.timestamp = time.time()
   
   def updateVol(self,newVol):
       self.volume = newVol


class OrderBook:
   def __init__(self):
      # price → deque of orders
      self.bids = SortedDict(lambda x: -x)  # descending
      self.asks = SortedDict()              # ascending
   
   def matchOrder(self,order):
      trades = []
      remainder = order
      opposite = self.bids if order.side == "S" else self.asks

      for price, queue in list(opposite.item()):
         if (order.side == 'buy' and order.price < price) or \
            (order.side == 'sell' and order.price > price):
            break
         while queue and remainder.volume > 0:
            match_order = queue[0]
            traded_vol = min(remainder.volume, match_order.volume)
            
