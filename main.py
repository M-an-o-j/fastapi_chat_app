from typing import List
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class ConnectionManager:
    # initialize list for websockets connections
    def __init__(self):
        self.active_rooms: dict = {}

    # accept and append the connection to the list
    async def connect(self, websocket: WebSocket, name: str):
        print(self.active_rooms)
        await websocket.accept()

        # Append the websocket to the list
        if name not in self.active_rooms:
            self.active_rooms[name] = websocket  
            print(self.active_rooms)

    # remove the connection from list
    def disconnect(self, websocket: WebSocket):
        for room_id, connections in self.active_rooms.items():
            # print(connections,"connctions")
            if websocket in connections:
                connections.remove(websocket)   
                if not connections:  # If no more connections in the room, remove the room
                    del self.active_rooms[room_id]
                break

    # send personal message to the connection
    async def send_personal_message(self, message: str, websocket: WebSocket):
        print(message)
        await websocket.send_text(message)

    # send message to the list of connections
    async def broadcast(self, message: str,room_id:int, websocket: WebSocket):
        for connection in self.active_rooms[room_id]:
            if (connection == websocket):
                continue
            await connection.send_text(message)


# instance for hndling and dealing with the websocket connections
connectionmanager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    # Render the HTML template
    return templates.TemplateResponse("chat.html", {"request": request})


@app.websocket("/ws/{name}")
async def websocket_endpoint(websocket: WebSocket,name:str):
    # accept connections
    await connectionmanager.connect(websocket, name)
    try:
        while True:
            # receive text from the user
            receiver = await websocket.receive_text()
            data = await websocket.receive_text()
            if receiver in connectionmanager.active_rooms:
                user = connectionmanager.active_rooms[receiver]
            else:
                await websocket.send_text("user not found")
            await connectionmanager.send_personal_message(f"{name} : {data}", user )
            # broadcast message to the connected user
            # await connectionmanager.broadcast(f"Client #{room_id}: {data}",room_id, websocket)

    # WebSocketDisconnect exception will be raised when client is disconnected
    except (WebSocketDisconnect,Exception) as e:
        connectionmanager.disconnect(websocket)
        # Broadcast a message indicating that the client has left the chat
        for room_id, connections in connectionmanager.active_rooms.items():
            if websocket in connections:
                await connectionmanager.broadcast(f"Client #{room_id} left the chat", room_id, websocket)
                break
