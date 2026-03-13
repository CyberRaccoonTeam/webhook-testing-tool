#!/usr/bin/env python3
from app import app, socketio

if __name__ == '__main__':
    socketio.run(app)
