// Webhook Testing Tool - Frontend

// State
let currentEndpointId = null;
let socket = null;

// DOM Elements
const createBtn = document.getElementById('create-endpoint-btn');
const endpointSection = document.getElementById('endpoint-section');
const webhooksSection = document.getElementById('webhooks-section');
const webhookUrlInput = document.getElementById('webhook-url');
const copyUrlBtn = document.getElementById('copy-url-btn');
const clearWebhooksBtn = document.getElementById('clear-webhooks-btn');
const webhooksList = document.getElementById('webhooks-list');
const requestCount = document.getElementById('request-count');
const webhookCount = document.getElementById('webhook-count');
const realtimeIndicator = document.getElementById('realtime-indicator');
const webhookModal = document.getElementById('webhook-modal');
const closeModalBtn = document.getElementById('close-modal-btn');

// API Base
const API_BASE = window.location.origin;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    setupEventListeners();
});

// Socket.io setup
function initSocket() {
    socket = io(API_BASE);
    
    socket.on('connect', () => {
        console.log('Connected to WebSocket');
    });
    
    socket.on('webhook_received', (data) => {
        console.log('Webhook received:', data);
        if (data.endpoint_id === currentEndpointId) {
            addWebhookToList(data, true);
            updateStats();
        }
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from WebSocket');
    });
}

// Event Listeners
function setupEventListeners() {
    createBtn.addEventListener('click', createEndpoint);
    copyUrlBtn.addEventListener('click', copyUrl);
    clearWebhooksBtn.addEventListener('click', clearWebhooks);
    closeModalBtn.addEventListener('click', closeModal);
    
    // Close modal on outside click
    webhookModal.addEventListener('click', (e) => {
        if (e.target === webhookModal) {
            closeModal();
        }
    });
    
    // Close modal on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// Create Endpoint
async function createEndpoint() {
    try {
        const response = await fetch(`${API_BASE}/api/endpoints`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        currentEndpointId = data.id;
        webhookUrlInput.value = data.full_url;
        
        // Show sections
        endpointSection.classList.remove('hidden');
        webhooksSection.classList.remove('hidden');
        realtimeIndicator.classList.remove('hidden');
        
        // Join WebSocket room
        socket.emit('join', { endpoint_id: currentEndpointId });
        
        // Update UI
        createBtn.textContent = '+ Create New Endpoint';
        webhooksList.innerHTML = '<p class="empty-state">Waiting for webhooks...</p>';
        
        console.log('Created endpoint:', data);
    } catch (error) {
        console.error('Error creating endpoint:', error);
        alert('Failed to create endpoint. Please try again.');
    }
}

// Copy URL
function copyUrl() {
    webhookUrlInput.select();
    document.execCommand('copy');
    
    const originalText = copyUrlBtn.textContent;
    copyUrlBtn.textContent = '✓ Copied!';
    copyUrlBtn.style.borderColor = '#00ff88';
    copyUrlBtn.style.color = '#00ff88';
    
    setTimeout(() => {
        copyUrlBtn.textContent = originalText;
        copyUrlBtn.style.borderColor = '';
        copyUrlBtn.style.color = '';
    }, 2000);
}

// Fetch Webhooks
async function fetchWebhooks() {
    if (!currentEndpointId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/endpoints/${currentEndpointId}/webhooks`);
        const webhooks = await response.json();
        
        if (webhooks.length === 0) {
            webhooksList.innerHTML = '<p class="empty-state">Waiting for webhooks...</p>';
            return;
        }
        
        webhooksList.innerHTML = '';
        webhooks.forEach(w => addWebhookToList(w, false));
        
    } catch (error) {
        console.error('Error fetching webhooks:', error);
    }
}

// Add Webhook to List
function addWebhookToList(webhook, isNew = false) {
    // Remove empty state
    const emptyState = webhooksList.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    const item = document.createElement('div');
    item.className = `webhook-item ${isNew ? 'new' : ''}`;
    item.dataset.id = webhook.id;
    
    const time = new Date(webhook.received_at).toLocaleTimeString();
    
    let preview = webhook.body || 'No body';
    if (preview.length > 100) {
        preview = preview.substring(0, 100) + '...';
    }
    
    item.innerHTML = `
        <div class="webhook-header">
            <span class="method-badge ${webhook.method}">${webhook.method}</span>
            <span class="webhook-time">${time}</span>
        </div>
        <div class="webhook-preview">${escapeHtml(preview)}</div>
    `;
    
    item.addEventListener('click', () => showWebhookDetail(webhook));
    
    // Add to top of list
    webhooksList.insertBefore(item, webhooksList.firstChild);
    
    // Remove 'new' class after animation
    if (isNew) {
        setTimeout(() => {
            item.classList.remove('new');
        }, 3000);
    }
}

// Show Webhook Detail
function showWebhookDetail(webhook) {
    document.getElementById('modal-title').textContent = `Webhook ${webhook.id}`;
    document.getElementById('modal-method').textContent = webhook.method;
    document.getElementById('modal-method').className = `method-badge ${webhook.method}`;
    document.getElementById('modal-time').textContent = new Date(webhook.received_at).toLocaleString();
    document.getElementById('modal-ip').textContent = webhook.ip_address || 'Unknown';
    
    // Format headers
    const headers = webhook.headers || {};
    document.getElementById('modal-headers').textContent = JSON.stringify(headers, null, 2);
    
    // Format query params
    const params = webhook.query_params || {};
    document.getElementById('modal-params').textContent = Object.keys(params).length > 0 
        ? JSON.stringify(params, null, 2) 
        : '{}';
    
    // Format body
    let body = webhook.body || '';
    try {
        const parsed = JSON.parse(body);
        body = JSON.stringify(parsed, null, 2);
    } catch (e) {
        // Not JSON, leave as is
    }
    document.getElementById('modal-body').textContent = body || '(empty)';
    
    webhookModal.classList.remove('hidden');
}

// Close Modal
function closeModal() {
    webhookModal.classList.add('hidden');
}

// Clear Webhooks
async function clearWebhooks() {
    if (!currentEndpointId) return;
    
    if (!confirm('Are you sure you want to delete this endpoint and all webhooks?')) {
        return;
    }
    
    try {
        await fetch(`${API_BASE}/api/endpoints/${currentEndpointId}`, {
            method: 'DELETE'
        });
        
        // Reset UI
        currentEndpointId = null;
        endpointSection.classList.add('hidden');
        webhooksSection.classList.add('hidden');
        realtimeIndicator.classList.add('hidden');
        
    } catch (error) {
        console.error('Error clearing webhooks:', error);
    }
}

// Update Stats
async function updateStats() {
    if (!currentEndpointId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/endpoints/${currentEndpointId}`);
        const data = await response.json();
        
        requestCount.textContent = `${data.request_count} requests`;
        webhookCount.textContent = `${data.webhook_count} webhooks`;
        
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}