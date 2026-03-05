import requests
#from models.order import Order
response = requests.get("http://localhost:8000/post-order?key=key_def456&side=S&sym=GOOGL&price=40&vol=20")
#response = requests.get("http://localhost:8000/")
print("STATUS:", response.status_code)
print("Reste:", response.json()["reste"])
i = 0
for l in response.json()["trades"]:
    i += 1
    print(f"trade {i}: {l}")

#o1 = Order("B", "GOOGL", 500, 5000, "key_abc123")
#
#verif, msg = o1.checkOrderBalance()
#
#if verif:
#    print(msg)
#else:
#    print(verif)
#    print(msg)



