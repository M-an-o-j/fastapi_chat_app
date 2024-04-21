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
    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()

        if room_id in self.active_rooms and len(self.active_rooms[room_id]) >= 2:
            # If there are already two connections in the room, reject the new connection
            await websocket.close()
            return "Room is full. You can't connect."


        # Append the websocket to the list
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = []  # Initialize the list if the key doesn't exist
        self.active_rooms[room_id].append(websocket)

    # remove the connection from list
    def disconnect(self, websocket: WebSocket):
        print("|hgjyh")
        for room_id, connections in self.active_rooms.items():
            print(connections,"connctions")
            if websocket in connections:
                connections.remove(websocket)   
                if not connections:  # If no more connections in the room, remove the room
                    del self.active_rooms[room_id]
                break

    # send personal message to the connection
    async def send_personal_message(self, message: str, websocket: WebSocket):
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


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int):
    # accept connections
    await connectionmanager.connect(websocket, room_id)
    # print(websocket.__dict__)
    print(connectionmanager.active_rooms)
    # await websocket.accept()
    try:
        while True:
            # receive text from the user
            data = await websocket.receive_text()
            # await connectionmanager.send_personal_message(f"You : {data}", websocket)
            # broadcast message to the connected user
            await connectionmanager.broadcast(f"Client #{room_id}: {data}",room_id, websocket)

    # WebSocketDisconnect exception will be raised when client is disconnected
    except (WebSocketDisconnect,Exception) as e:
        connectionmanager.disconnect(websocket)
        # Broadcast a message indicating that the client has left the chat
        for room_id, connections in connectionmanager.active_rooms.items():
            if websocket in connections:
                await connectionmanager.broadcast(f"Client #{room_id} left the chat", room_id, websocket)
                break

