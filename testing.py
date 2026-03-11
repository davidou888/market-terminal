import requests
import random
import time
from config import get_db




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






#listeTest = [err1(), err2(), err3(), err4(), err5() ]

#for i in listeTest:
#    i




def test1():
    testType = "in pos"
    
    user_api_key_buyer = "7ab0bc97-e610-4311-8e4a-299653161e7d"
    user_api_key_seller = "38f1b94f-4e51-493c-93e1-2b1f47bd9fcb"
    stock = "WABERSCOIN"

    conn, cursor = get_db()
    cursor.execute("SELECT * FROM positions WHERE user_api_key = %s AND symbol = %s", (user_api_key_buyer, stock))
    rowInitBuy = cursor.fetchall()
    cursor.execute("SELECT * FROM positions WHERE user_api_key = %s AND symbol = %s", (user_api_key_seller, stock))
    rowInitSell = cursor.fetchall()
    conn.close()


    response1 = requests.get(f"http://localhost:8000/post-order?key={user_api_key_buyer}&side=B&sym={stock}&price=120&vol=10")
    response2 = requests.get(f"http://localhost:8000/post-order?key={user_api_key_seller}&side=S&sym={stock}&price=120&vol=3")
    #print(f"Status: {response.status_code}")
    print(f"Raw1: {response1.text}")
    print(f"Raw2: {response2.text}")

    conn, cursor = get_db()
    cursor.execute("SELECT * FROM positions WHERE user_api_key = %s AND symbol = %s", (user_api_key_buyer, stock))
    rowFinalBuy = cursor.fetchall()
    cursor.execute("SELECT * FROM positions WHERE user_api_key = %s AND symbol = %s", (user_api_key_seller, stock))
    rowFinalSell = cursor.fetchall()
    conn.close()

    print(testType)

    if not rowInitBuy:
        print(f"new pos buyer: {rowFinalBuy}")
    
    if not rowInitSell:
        print(f"new pos Seller: {rowFinalSell}")

    if not rowFinalBuy or not rowFinalSell:
        print(f"missing row final for buy: {rowFinalBuy} or sell: {rowFinalSell}")

    if rowInitBuy:
        print(f"pos init buy was: {rowInitBuy}")
        print(f"pos final buy is: {rowFinalBuy}")
    if rowInitSell:
        print(f"pos init sell was: {rowInitSell}")
        print(f"pos final sell is: {rowFinalSell}")

    else:
        print("What in the actual f*** ?")


print("------start test1----")
test1()
print("----end test1-----")
    

    