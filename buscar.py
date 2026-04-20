import http.client
import json
from dotenv import load_dotenv
import os

load_dotenv()

def buscar(pregunta):
    conn = http.client.HTTPSConnection("google.serper.dev")
    payload = json.dumps({
    "q": pregunta,
    "gl": "co",
    "hl": "es-419"
    })
    headers = {
    'X-API-KEY': os.getenv("API_KEY"),
    'Content-Type': 'application/json'
    }
    conn.request("POST", "/search", payload, headers)
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode("utf-8"))



