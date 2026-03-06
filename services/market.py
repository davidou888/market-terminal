import gevent
from extension import socketio

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
    socketio.emit("game_end", {"running": gameState["running"]})

"""
--------------------------------------------
Might modify this later, for prod compliance
"""
class Symbols:
    def __init__(self, name, price, final_price):
        self.name = name
        self.price = price
        self.final_price = final_price

Symbols_list = [
    Symbols("GOOGL", 4000, 4000),
    Symbols("AMZN", 3000, 3000)
]
"""
---------------------------------------------
"""

def createGame():
    if not gameState["running"] and gameState["start_trigger"]:
        print("[GAME]: Starting new game...")
        gameState["symbols"] = Symbols_list.copy()
        #broadcast game start to clients with initial symbol list and game state
        socketio.emit("game_start", {"symbols": [{"name": s.name, "price": s.price} for s in gameState["symbols"]], "running": gameState["running"]})
        gevent.spawn(countdown, 600)  # Start a 10-minute countdown

    else:
        print("[GAME]: Game already running or start trigger not set.")
