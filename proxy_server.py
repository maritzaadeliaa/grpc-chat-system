import os
import asyncio
import logging
import grpc
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import concurrent.futures

import user_pb2
import user_pb2_grpc
import room_pb2
import room_pb2_grpc
import chat_pb2
import chat_pb2_grpc

app = FastAPI(title="gRPC Chat Proxy")
global_executor = concurrent.futures.ThreadPoolExecutor(max_workers=20)

# Serve the web frontend if the folder exists
os.makedirs("web", exist_ok=True)
app.mount("/app", StaticFiles(directory="web", html=True), name="web")

logging.basicConfig(level=logging.INFO)

# Connect to gRPC channels
try:
    user_channel = grpc.insecure_channel('localhost:50052')
    user_stub = user_pb2_grpc.UserServiceStub(user_channel)
    
    room_channel = grpc.insecure_channel('localhost:50053')
    room_stub = room_pb2_grpc.RoomServiceStub(room_channel)
    
    chat_channel = grpc.insecure_channel('localhost:50051')
    chat_stub = chat_pb2_grpc.ChatServiceStub(chat_channel)
except Exception as e:
    logging.error(f"Failed to connect to gRPC: {e}")

@app.websocket("/ws/{username}/{room}")
async def websocket_chat_endpoint(websocket: WebSocket, username: str, room: str):
    await websocket.accept()
    logging.info(f"WebSocket connected for {username} in {room}")
    loop = asyncio.get_running_loop()
    
    # Run Login
    try:
        def do_login_and_join():
            # Synchronous blocks inside a thread
            l_res = user_stub.Login(user_pb2.UserRequest(username=username), timeout=2)
            if l_res.status != "SUCCESS":
                return False, l_res, None
            j_res = room_stub.JoinRoom(room_pb2.RoomRequest(username=username, room=room), timeout=2)
            return True, l_res, j_res

        success, login_res, join_res = await loop.run_in_executor(global_executor, do_login_and_join)
        
        await websocket.send_json({"type": "login_status", "status": login_res.status, "message": login_res.message})
        if not success:
            await websocket.close()
            return

        if join_res and join_res.status != "SUCCESS":
            await websocket.send_json({"type": "system", "message": join_res.message})
            await websocket.close()
            return
        elif join_res:
             await websocket.send_json({"type": "system", "message": join_res.message})
            
    except Exception as e:
        logging.error(f"gRPC connection error: {e}")
        await websocket.send_json({"type": "error", "message": f"gRPC connection error: {str(e)}"})
        await websocket.close()
        return

    # Queue for messages from Websocket to gRPC
    import queue
    message_queue = queue.Queue()
    
    def generate_messages():
        # Kirim dummy message agar gRPC server langsung me-register user ini ke room
        yield chat_pb2.ChatMessage(
            username=username,
            room=room,
            message="[JOIN]"
        )
        while True:
            try:
                msg = message_queue.get(timeout=1.0)
                if msg is None:
                    break
                yield chat_pb2.ChatMessage(
                    username=username,
                    room=room,
                    message=msg
                )
            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error yielding message: {e}")
                break

    def grpc_listen(listen_loop):
        try:
            responses = chat_stub.ChatStream(generate_messages())
            for response in responses:
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "chat", "username": response.username, "message": response.message}),
                    listen_loop
                )
        except Exception as e:
            logging.error(f"gRPC Listen disconnected: {e}")
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.send_json({"type": "system", "message": "Disconnected from server."}),
                    listen_loop
                )
            except:
                pass

    try:
        grpc_future = loop.run_in_executor(global_executor, grpc_listen, loop)
        
        while True:
            data = await websocket.receive_text()
            message_queue.put(data)
            
    except WebSocketDisconnect:
        logging.info(f"{username} disconnected")
        message_queue.put(None)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        message_queue.put(None)
    finally:
        # Call Logout on backend to release the username
        try:
            def do_logout():
                user_stub.Logout(user_pb2.UserRequest(username=username), timeout=2)
            await loop.run_in_executor(global_executor, do_logout)
        except Exception as e:
            logging.error(f"Logout error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("proxy_server:app", host="0.0.0.0", port=8000, reload=True)
