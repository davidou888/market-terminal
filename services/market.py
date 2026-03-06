import gevent
from extension import socketio
from services.trade import getSymbolsData

#------- GAME LOGIC -------#

gameState = {
    "time_left": 0,
    "running": False,
    "start_trigger": True,
    "symbols": []
}

def countdown(time_sec=0):
    if time_sec >0:
        gameState["time_left"] = time_sec
        gameState["running"] = True
    while gameState["time_left"] > 0:
        gevent.sleep(1)
        gameState["time_left"] -= 1
        #broadcast time update to clients
        socketio.emit("time_update", {"time_left": gameState["time_left"]})
    gameState["running"] = False
    socketio.emit("game_end", {"running": gameState["running"], "symbols": [{"name": s.name, "final_price": s.final_price} for s in gameState["symbols"]]})

"""
--------------------------------------------
Might modify this later, for prod compliance
"""
class Symbols:
    def __init__(self, name, price, final_price):
        self.name = name
        self.price = price
        self.final_price = final_price

"""
---------------------------------------------
"""

def createGame():
    if not gameState["running"] and gameState["start_trigger"]:
        print("[GAME]: Starting new game...")
        rows = getSymbolsData()
        gameState["symbols"] = [Symbols(r[0], float(r[1]), float(r[2])) for r in rows]
        print(f"[GAME]: Symbols loaded: {[s.name for s in gameState['symbols']]}")
        #broadcast game start to clients with initial symbol list and game state
        socketio.emit("game_start", {"symbols": [{"name": s.name, "price": s.price} for s in gameState["symbols"]], "running": gameState["running"]})
        gevent.spawn(countdown, 600)  # Start a 10-minute countdown

    else:
        print("[GAME]: Game already running or start trigger not set.")
