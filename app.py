# app.py
from fastapi import FastAPI
from aiohttp import web
import socketio    

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

#from fastapi_socketio import SocketManager

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi')    
socket_app = socketio.ASGIApp(sio, static_files={'/': 'viewer/index.html'})    
background_task_started = False 

#sio = SocketManager(app=app)
#sio.attach(app)

async def background_task(): 
    print("background task")

@sio.on('disconnect')
def test_disconnect(sid):
    print('Client disconnected')


@app.get("/hello")
async def root():
    return {"message": "Hello World"}


app.mount("/static", StaticFiles(directory="viewer"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")


app.mount('/', socket_app)

#@app.get("/viewer", response_class=HTMLResponse)
#async def index():
#    with open('viewer/index.html') as f:
#        return f.read()


@sio.on('syncTrajectory')
async def handle_join(sid, *args, **kwargs):
    print("JOINING")
    print(sid)
    print(args)
    await sio.emit('lobby', 'User joined')


# @sio.on('test')
# async def test(sid, *args, **kwargs):
#     await sio.emit('hey', 'joe')

#app.router.add_get('/', index)


if __name__ == '__main__':
    import logging
    import sys

    logging.basicConfig(level=logging.DEBUG,
                        stream=sys.stdout)

    import uvicorn

    uvicorn.run("app:app", host='0.0.0.0', port=8000, reload=True, debug=True,log_level="debug")
