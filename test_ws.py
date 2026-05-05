from fastapi.testclient import TestClient
from app.main import app

def test_ws():
    client = TestClient(app)
    try:
        with client.websocket_connect("/v1/audio/stream") as websocket:
            print("Connected!")
            websocket.send_bytes(b'\x1aE\xdf\xa3' + b'fake data')
            data = websocket.receive_json()
            print("Received:", data)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ws()
