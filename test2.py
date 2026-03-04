import requests

response = requests.get("http://localhost:8000/post-order?key=key_abc123&side=B&sym=GOOGL&price=40&vol=10")
#response = requests.get("http://localhost:8000/")
print("STATUS:", response.status_code)
print("Reste:", response.json()["reste"])
i = 0
for l in response.json()["trades"]:
    i += 1
    print(f"trade {i}: {l}")

