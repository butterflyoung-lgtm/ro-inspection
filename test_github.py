import urllib.request
import json
import base64

# Test GitHub public repo creation or gist
def check_github():
    url = "https://api.github.com/zen"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Python"})
        res = urllib.request.urlopen(req)
        print("GitHub connectivity:", res.read().decode())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    check_github()
