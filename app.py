#!/usr/bin/env python3
"""
Webhook Testing Tool - MVP
Test and debug webhooks in real-time
"""

import os
import json
import uuid
import hashlib
import hmac
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'webhook-tool-secret-key-2026')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DATABASE = 'webhooks.db'

# Database setup
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS endpoints (
            id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            request_count INTEGER DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS webhooks (
            id TEXT PRIMARY KEY,
            endpoint_id TEXT,
            method TEXT,
            headers TEXT,
            body TEXT,
            query_params TEXT,
            ip_address TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (endpoint_id) REFERENCES endpoints(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Helper functions
def generate_endpoint_id():
    return uuid.uuid4().hex[:12]

def generate_webhook_id():
    return uuid.uuid4().hex[:16]

# Routes
@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/endpoints', methods=['POST'])
def create_endpoint():
    """Create a new webhook endpoint"""
    endpoint_id = generate_endpoint_id()
    conn = get_db()
    conn.execute(
        'INSERT INTO endpoints (id, created_at) VALUES (?, ?)',
        (endpoint_id, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        'id': endpoint_id,
        'url': f'/webhook/{endpoint_id}',
        'full_url': f'http://localhost:5559/webhook/{endpoint_id}',
        'created_at': datetime.utcnow().isoformat()
    }), 201

@app.route('/api/endpoints/<endpoint_id>', methods=['GET'])
def get_endpoint(endpoint_id):
    """Get endpoint details"""
    conn = get_db()
    endpoint = conn.execute(
        'SELECT * FROM endpoints WHERE id = ?', (endpoint_id,)
    ).fetchone()
    
    if not endpoint:
        conn.close()
        return jsonify({'error': 'Endpoint not found'}), 404
    
    webhook_count = conn.execute(
        'SELECT COUNT(*) as count FROM webhooks WHERE endpoint_id = ?',
        (endpoint_id,)
    ).fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'id': endpoint['id'],
        'created_at': endpoint['created_at'],
        'last_accessed': endpoint['last_accessed'],
        'request_count': endpoint['request_count'],
        'webhook_count': webhook_count
    })

@app.route('/api/endpoints/<endpoint_id>/webhooks', methods=['GET'])
def get_webhooks(endpoint_id):
    """Get all webhooks for an endpoint"""
    conn = get_db()
    webhooks = conn.execute(
        '''SELECT * FROM webhooks 
           WHERE endpoint_id = ? 
           ORDER BY received_at DESC 
           LIMIT 100''',
        (endpoint_id,)
    ).fetchall()
    conn.close()
    
    result = []
    for w in webhooks:
        result.append({
            'id': w['id'],
            'method': w['method'],
            'headers': json.loads(w['headers']) if w['headers'] else {},
            'body': w['body'],
            'query_params': json.loads(w['query_params']) if w['query_params'] else {},
            'ip_address': w['ip_address'],
            'received_at': w['received_at']
        })
    
    return jsonify(result)

@app.route('/api/endpoints/<endpoint_id>/export', methods=['GET'])
def export_webhooks(endpoint_id):
    """Export webhook history as JSON"""
    conn = get_db()
    webhooks = conn.execute(
        'SELECT * FROM webhooks WHERE endpoint_id = ? ORDER BY received_at DESC',
        (endpoint_id,)
    ).fetchall()
    conn.close()
    
    result = []
    for w in webhooks:
        result.append({
            'id': w['id'],
            'method': w['method'],
            'headers': json.loads(w['headers']) if w['headers'] else {},
            'body': w['body'],
            'query_params': json.loads(w['query_params']) if w['query_params'] else {},
            'ip_address': w['ip_address'],
            'received_at': w['received_at']
        })
    
    return jsonify({
        'endpoint_id': endpoint_id,
        'exported_at': datetime.utcnow().isoformat(),
        'webhooks': result
    })

@app.route('/api/endpoints/<endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    """Delete an endpoint and all its webhooks"""
    conn = get_db()
    conn.execute('DELETE FROM webhooks WHERE endpoint_id = ?', (endpoint_id,))
    conn.execute('DELETE FROM endpoints WHERE id = ?', (endpoint_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Endpoint deleted'})

@app.route('/webhook/<endpoint_id>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def receive_webhook(endpoint_id):
    """Receive a webhook payload"""
    conn = get_db()
    
    # Check if endpoint exists
    endpoint = conn.execute(
        'SELECT * FROM endpoints WHERE id = ?', (endpoint_id,)
    ).fetchone()
    
    if not endpoint:
        conn.close()
        return jsonify({'error': 'Endpoint not found'}), 404
    
    # Capture webhook data
    webhook_id = generate_webhook_id()
    
    # Get headers (exclude some internal ones)
    headers = {}
    for key, value in request.headers:
        if key.lower() not in ['host', 'content-length']:
            headers[key] = value
    
    # Get body
    try:
        body = request.get_data(as_text=True)
    except:
        body = ''
    
    # Get query params
    query_params = dict(request.args)
    
    # Store webhook
    conn.execute(
        '''INSERT INTO webhooks 
           (id, endpoint_id, method, headers, body, query_params, ip_address, received_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (webhook_id, endpoint_id, request.method, 
         json.dumps(headers), body, json.dumps(query_params),
         request.remote_addr, datetime.utcnow().isoformat())
    )
    
    # Update endpoint stats
    conn.execute(
        '''UPDATE endpoints 
           SET last_accessed = ?, request_count = request_count + 1
           WHERE id = ?''',
        (datetime.utcnow().isoformat(), endpoint_id)
    )
    
    conn.commit()
    conn.close()
    
    # Emit real-time update via WebSocket
    socketio.emit('webhook_received', {
        'id': webhook_id,
        'endpoint_id': endpoint_id,
        'method': request.method,
        'headers': headers,
        'body': body,
        'query_params': query_params,
        'ip_address': request.remote_addr,
        'received_at': datetime.utcnow().isoformat()
    }, room=endpoint_id)
    
    return jsonify({
        'status': 'received',
        'webhook_id': webhook_id,
        'endpoint_id': endpoint_id
    })

@app.route('/api/webhooks/<webhook_id>', methods=['GET'])
def get_webhook_detail(webhook_id):
    """Get details of a specific webhook"""
    conn = get_db()
    webhook = conn.execute(
        'SELECT * FROM webhooks WHERE id = ?', (webhook_id,)
    ).fetchone()
    conn.close()
    
    if not webhook:
        return jsonify({'error': 'Webhook not found'}), 404
    
    return jsonify({
        'id': webhook['id'],
        'endpoint_id': webhook['endpoint_id'],
        'method': webhook['method'],
        'headers': json.loads(webhook['headers']) if webhook['headers'] else {},
        'body': webhook['body'],
        'query_params': json.loads(webhook['query_params']) if webhook['query_params'] else {},
        'ip_address': webhook['ip_address'],
        'received_at': webhook['received_at']
    })

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('join')
def on_join(data):
    """Join a room for a specific endpoint"""
    endpoint_id = data.get('endpoint_id')
    if endpoint_id:
        from flask_socketio import join_room
        join_room(endpoint_id)
        emit('joined', {'endpoint_id': endpoint_id})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

if __name__ == '__main__':
    print('🪝 Webhook Testing Tool starting on port 5559...')
    socketio.run(app, host='0.0.0.0', port=5559, debug=True, allow_unsafe_werkzeug=True)