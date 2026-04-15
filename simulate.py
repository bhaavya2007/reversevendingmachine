import requests

while True:
    input("Press ENTER to simulate garbage throw...")
    res = requests.get("http://127.0.0.1:5000/generate_code")
    print(res.text)
