import requests
import random
import time




Ldt = []

def stressTest(n):

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
    print(f"max response time: {max(Ldt):.4f}s")


def err1():
    errType = "Price > balance"
    response = requests.get("http://localhost:8000/post-order?key=key_def456&side=B&sym=GOOGL&price=4000&vol=2000")
    print(f"Status: {response.status_code}")
    print(f"Raw: {response.text}") 
    if (response.json()["error"]):
        print(errType)
        print(f"[ERROR]: {response.json()["error"]}")

    else:
        print(errType)
        print(f"NO ERROR... ")

def err2():
    errType = "Price < 0"
    response = requests.get("http://localhost:8000/post-order?key=key_def456&side=B&sym=GOOGL&price=-10&vol=20")
    print(f"Status: {response.status_code}")
    print(f"Raw: {response.text}")
    if (response.json()["error"]):
        print(errType)
        print(f"[ERROR]: {response.json()["error"]}")
    else:
        print(errType)
        print(f"NO ERROR... ")

def err3():
    errType = "Vol < 0"
    response = requests.get("http://localhost:8000/post-order?key=key_def456&side=B&sym=GOOGL&price=10&vol=-20")
    print(f"Status: {response.status_code}")
    print(f"Raw: {response.text}")
    if (response.json()["error"]):
        print(errType)
        print(f"[ERROR]: {response.json()["error"]}")

    else:
        print(errType)
        print(f"NO ERROR... ")

def err4():
    errType = "bad key"
    response = requests.get("http://localhost:8000/post-order?key=blabla&side=B&sym=GOOGL&price=10&vol=20")
    print(f"Status: {response.status_code}")
    print(f"Raw: {response.text}")
    if (response.json()["error"]):
        print(errType)
        print(f"[ERROR]: {response.json()["error"]}")

    else:
        print(errType)
        print(f"NO ERROR... ")

def err5():
    errType = "bad symbol"
    response = requests.get("http://localhost:8000/post-order?key=key_def456&side=B&sym=chaise&price=10&vol=20")
    print(f"Status: {response.status_code}")
    print(f"Raw: {response.text}")
    if (response.json()["error"]):
        print(errType)
        print(f"[ERROR]: {response.json()["error"]}")

    else:
        print(errType)
        print(f"NO ERROR... ")




listeTest = [err1(), err2(), err3(), err4(), err5() ]

for i in listeTest:
    i