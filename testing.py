import requests
import random
import time

Ldt = []

for i in range(500):
    
    ti = time.time()
    rdm = random.randint(60,100)
    rdmSide = random.choice(["S","B"])
    rdmVol = random.randint(10,40)
    response = requests.get(f"http://localhost:8000/post-order?key=key_abc123&side={rdmSide}&sym=GOOGL&price={rdm}&vol={rdmVol}")
    #response = requests.get("http://localhost:8000/")
    #print("STATUS:", response.status_code)
    print("TEXT:", response.text)
    tf = time.time()
    delta = tf -ti
    Ldt.append(delta)  


print(f"avg response time: {sum(Ldt)/len(Ldt):.4f}s") #0.0809s
print(f"max response time: {max(Ldt):.4f}s")    #0.1519s



