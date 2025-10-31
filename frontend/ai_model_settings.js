// AI Model Settings JavaScript

const API_BASE = window.location.origin;
let allModels = {};
let currentDefaultModel = '';
let modelStatuses = {};
let activeFilters = {
    provider: 'all',
    availability: 'all'
};

// Global state for API key modal
let currentConfigModel = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    initializeApiKeyModal();
    loadModels();
    loadProviderSummary();
});

// Initialize filter buttons
function initializeFilters() {
    // Provider filters
    document.querySelectorAll('[data-provider]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-provider]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilters.provider = btn.dataset.provider;
            filterModels();
        });
    });
    
    // Availability filters
    document.querySelectorAll('[data-availability]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('[data-availability]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilters.availability = btn.dataset.availability;
            filterModels();
        });
    });
    
    // Modal close
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('model-modal').style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('model-modal');
        const apiKeyModal = document.getElementById('api-key-modal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
        if (e.target === apiKeyModal) {
            apiKeyModal.style.display = 'none';
        }
    });
}

// Initialize API Key Modal
function initializeApiKeyModal() {
    // Close button
    document.querySelector('.close-api-key').addEventListener('click', () => {
        document.getElementById('api-key-modal').style.display = 'none';
    });
    
    // Toggle visibility button
    document.getElementById('toggle-api-key-visibility').addEventListener('click', () => {
        const input = document.getElementById('api-key-input');
        const button = document.getElementById('toggle-api-key-visibility');
        
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '🙈 Hide';
        } else {
            input.type = 'password';
            button.textContent = '👁️ Show';
        }
    });
    
    // Save button
    document.getElementById('save-api-key-btn').addEventListener('click', saveApiKey);
    
    // Cancel button
    document.getElementById('cancel-api-key-btn').addEventListener('click', () => {
        document.getElementById('api-key-modal').style.display = 'none';
    });
}

// Load all models
async function loadModels() {
    try {
        const response = await fetch(`${API_BASE}/api/ai-models/list`);
        const data = await response.json();
        
        if (data.success) {
            allModels = data.models;
            currentDefaultModel = data.default_model;
            
            // Test all models
            await testAllModels();
            
            // Display current default
            displayCurrentDefault();
            
            // Display all models
            displayModels();
        }
    } catch (error) {
        showToast('Error loading models: ' + error.message, 'error');
        console.error('Error loading models:', error);
    }
}

// Test all models for availability
async function testAllModels() {
    const modelIds = Object.keys(allModels);
    const testPromises = modelIds.map(async (modelId) => {
        try {
            const response = await fetch(`${API_BASE}/api/ai-models/${modelId}/test`, {
                method: 'POST'
            });
            const result = await response.json();
            modelStatuses[modelId] = result;
        } catch (error) {
            modelStatuses[modelId] = { available: false, message: 'Test failed' };
        }
    });
    
    await Promise.all(testPromises);
}

// Display current default model
function displayCurrentDefault() {
    const currentModelCard = document.getElementById('current-model-card');
    const model = allModels[currentDefaultModel];
    const status = modelStatuses[currentDefaultModel] || {};
    
    if (!model) {
        currentModelCard.innerHTML = '<p>No default model set</p>';
        return;
    }
    
    const statusClass = status.available ? 'available' : 'unavailable';
    const statusText = status.available ? '✅ Available' : '⚠️ Unavailable';
    
    currentModelCard.innerHTML = `
        <h3>${model.display_name}</h3>
        <p style="opacity: 0.9; margin-top: 10px;">${model.description}</p>
        <div class="model-meta">
            <span class="badge">${model.provider.toUpperCase()}</span>
            <span class="badge">${model.is_local ? '🏠 Local' : '☁️ Cloud'}</span>
            <span class="badge">${statusText}</span>
            <span class="badge">💰 $${model.capabilities.cost_per_1m_tokens}/1M tokens</span>
        </div>
    `;
}

// Display all models
function displayModels() {
    const grid = document.getElementById('models-grid');
    const modelIds = Object.keys(allModels);
    
    if (modelIds.length === 0) {
        grid.innerHTML = '<p>No models available</p>';
        return;
    }
    
    grid.innerHTML = modelIds.map(modelId => createModelCard(modelId)).join('');
    
    // Add event listeners
    document.querySelectorAll('.model-card').forEach(card => {
        const modelId = card.dataset.modelId;
        
        // Configure button
        card.querySelector('.btn-configure')?.addEventListener('click', (e) => {
            e.stopPropagation();
            showApiKeyModal(modelId);
        });
        
        // Set as default button
        card.querySelector('.btn-primary:not(.btn-configure)')?.addEventListener('click', (e) => {
            e.stopPropagation();
            setAsDefault(modelId);
        });
        
        // Details button
        card.querySelector('.btn-secondary')?.addEventListener('click', (e) => {
            e.stopPropagation();
            showModelDetails(modelId);
        });
    });
}

// Show API Key Modal
function showApiKeyModal(modelId) {
    currentConfigModel = modelId;
    const model = allModels[modelId];
    
    // Update modal content
    document.getElementById('api-key-model-name').textContent = `Configure API key for ${model.display_name}`;
    document.getElementById('api-key-input').value = '';
    document.getElementById('api-key-validation-result').style.display = 'none';
    
    // Set help text based on provider
    const provider = model.provider;
    const helpTexts = {
        'openai': 'Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank">platform.openai.com/api-keys</a>',
        'anthropic': 'Get your API key from <a href="https://console.anthropic.com/settings/keys" target="_blank">console.anthropic.com/settings/keys</a>',
        'google': 'Get your API key from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a>'
    };
    
    document.getElementById('api-key-help-text').innerHTML = helpTexts[provider] || 'Consult your provider\'s documentation for API key information.';
    
    // Show modal
    document.getElementById('api-key-modal').style.display = 'block';
}

// Save API Key
async function saveApiKey() {
    const apiKey = document.getElementById('api-key-input').value.trim();
    const saveBtn = document.getElementById('save-api-key-btn');
    const resultDiv = document.getElementById('api-key-validation-result');
    
    if (!apiKey) {
        resultDiv.className = 'error';
        resultDiv.textContent = 'Please enter an API key';
        resultDiv.style.display = 'block';
        return;
    }
    
    // Show loading state
    saveBtn.disabled = true;
    saveBtn.textContent = 'Validating...';
    resultDiv.style.display = 'none';
    
    try {
        const response = await fetch(`${API_BASE}/api/ai-models/${currentConfigModel}/configure`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const data = await response.json();
        
        if (data.success && data.validation?.available) {
            // Success!
            resultDiv.className = 'success';
            resultDiv.textContent = '✅ API key validated and saved successfully!';
            resultDiv.style.display = 'block';
            
            showToast('API key configured successfully!', 'success');
            
            // Reload models to update status
            setTimeout(() => {
                document.getElementById('api-key-modal').style.display = 'none';
                loadModels();
            }, 1500);
        } else {
            // Validation failed
            resultDiv.className = 'error';
            resultDiv.textContent = `❌ ${data.validation?.message || data.error || 'API key validation failed'}`;
            resultDiv.style.display = 'block';
        }
    } catch (error) {
        resultDiv.className = 'error';
        resultDiv.textContent = `❌ Error: ${error.message}`;
        resultDiv.style.display = 'block';
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save & Validate';
    }
}

// Create model card HTML
function createModelCard(modelId) {
    const model = allModels[modelId];
    const status = modelStatuses[modelId] || {};
    const isDefault = modelId === currentDefaultModel;
    const isAvailable = status.available || false;
    const requiresApiKey = !model.is_local;
    const isConfigured = isAvailable || model.is_local;
    
    const cardClasses = [
        'model-card',
        isDefault ? 'default' : '',
        !isAvailable ? 'unavailable' : ''
    ].filter(c => c).join(' ');
    
    const capabilities = model.capabilities || {};
    
    return `
        <div class="${cardClasses}" data-model-id="${modelId}">
            <div class="model-card-header">
                <div>
                    <h3>${model.display_name}</h3>
                    <span class="provider-badge ${model.provider}">${model.provider.toUpperCase()}</span>
                </div>
            </div>
            
            <p class="description">${model.description}</p>
            
            <div class="capabilities">
                <div class="capability-item">
                    <span class="icon">💰</span>
                    <span>${capabilities.cost_per_1m_tokens === 0 ? 'Free' : '$' + capabilities.cost_per_1m_tokens + '/1M'}</span>
                </div>
                <div class="capability-item">
                    <span class="icon">⚡</span>
                    <span>${capabilities.speed || 'N/A'}</span>
                </div>
                <div class="capability-item">
                    <span class="icon">⭐</span>
                    <span>${capabilities.quality || 'N/A'} quality</span>
                </div>
                <div class="capability-item">
                    <span class="icon">${model.is_local ? '🏠' : '☁️'}</span>
                    <span>${model.is_local ? 'Local' : 'Cloud'}</span>
                </div>
            </div>
            
            ${isDefault ? '<span class="status-badge default">⭐ DEFAULT MODEL</span>' : ''}
            ${!isDefault && isAvailable ? '<span class="status-badge available">✅ Available</span>' : ''}
            ${!isAvailable ? `<span class="status-badge unavailable">⚠️ Unavailable</span>` : ''}
            
            ${requiresApiKey ? (isConfigured ? '<span class="configured-badge">🔑 Configured</span>' : '<span class="needs-config-badge">🔑 Needs API Key</span>') : ''}
            
            ${!isAvailable && status.suggestion ? `<p style="color: #ef4444; font-size: 0.85rem; margin-top: 10px;">💡 ${status.suggestion}</p>` : ''}
            
            <div class="actions">
                ${requiresApiKey && !isConfigured ? 
                    `<button class="btn btn-configure" data-model-id="${modelId}">Configure API Key</button>` :
                    !isDefault && isAvailable ? 
                        `<button class="btn btn-primary">Set as Default</button>` : 
                        `<button class="btn btn-primary" disabled>${isDefault ? 'Current Default' : 'Unavailable'}</button>`
                }
                <button class="btn btn-secondary">Details</button>
            </div>
        </div>
    `;
}

// Filter models based on active filters
function filterModels() {
    const cards = document.querySelectorAll('.model-card');
    
    cards.forEach(card => {
        const modelId = card.dataset.modelId;
        const model = allModels[modelId];
        const status = modelStatuses[modelId] || {};
        
        let show = true;
        
        // Provider filter
        if (activeFilters.provider !== 'all' && model.provider !== activeFilters.provider) {
            show = false;
        }
        
        // Availability filter
        if (activeFilters.availability === 'available' && !status.available) {
            show = false;
        }
        
        card.style.display = show ? 'block' : 'none';
    });
}

// Set model as default
async function setAsDefault(modelId) {
    try {
        const response = await fetch(`${API_BASE}/api/ai-models/default`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ model_id: modelId })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`✅ ${allModels[modelId].display_name} set as default!`, 'success');
            currentDefaultModel = modelId;
            
            // Refresh display
            displayCurrentDefault();
            displayModels();
        } else {
            showToast('Error setting default model', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
        console.error('Error setting default:', error);
    }
}

// Show model details in modal
async function showModelDetails(modelId) {
    const modal = document.getElementById('model-modal');
    const modalBody = document.getElementById('modal-body');
    
    try {
        const response = await fetch(`${API_BASE}/api/ai-models/${modelId}`);
        const data = await response.json();
        
        if (data.success) {
            const model = data.model;
            const status = modelStatuses[modelId] || {};
            const config = model.config;
            const capabilities = config.capabilities || {};
            
            modalBody.innerHTML = `
                <h2>${config.display_name}</h2>
                <p style="color: #666; margin-bottom: 20px;">${config.description}</p>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px;">Status</h3>
                    <p><strong>Availability:</strong> ${status.available ? '✅ Available' : '⚠️ Unavailable'}</p>
                    <p><strong>Message:</strong> ${status.message || 'N/A'}</p>
                    ${status.suggestion ? `<p style="color: #ef4444;"><strong>Suggestion:</strong> ${status.suggestion}</p>` : ''}
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px;">Capabilities</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <p><strong>Max Tokens:</strong> ${capabilities.max_tokens?.toLocaleString() || 'N/A'}</p>
                        <p><strong>Context Window:</strong> ${capabilities.context_window?.toLocaleString() || 'N/A'}</p>
                        <p><strong>Speed:</strong> ${capabilities.speed || 'N/A'}</p>
                        <p><strong>Quality:</strong> ${capabilities.quality || 'N/A'}</p>
                        <p><strong>Cost:</strong> $${capabilities.cost_per_1m_tokens}/1M tokens</p>
                        <p><strong>Streaming:</strong> ${capabilities.supports_streaming ? 'Yes' : 'No'}</p>
                        <p><strong>Vision:</strong> ${capabilities.supports_vision ? 'Yes' : 'No'}</p>
                        <p><strong>Functions:</strong> ${capabilities.supports_function_calling ? 'Yes' : 'No'}</p>
                    </div>
                </div>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
                    <h3 style="margin-bottom: 15px;">Provider Information</h3>
                    <p><strong>Provider:</strong> ${model.provider_info.name}</p>
                    <p><strong>Type:</strong> ${config.is_local ? 'Local' : 'Cloud'}</p>
                    <p><strong>Cost Model:</strong> ${model.provider_info.cost_model}</p>
                    <p><strong>Requires API Key:</strong> ${model.provider_info.requires_api_key ? 'Yes' : 'No'}</p>
                    ${config.setup_instructions ? `<p><strong>Setup:</strong> ${config.setup_instructions}</p>` : ''}
                </div>
                
                <div style="display: flex; gap: 10px;">
                    ${model.is_default ? 
                        '<button class="btn btn-primary" disabled>Current Default</button>' :
                        status.available ? 
                            `<button class="btn btn-primary" onclick="setAsDefaultFromModal('${modelId}')">Set as Default</button>` :
                            '<button class="btn btn-primary" disabled>Unavailable</button>'
                    }
                    <button class="btn btn-secondary" onclick="testModelFromModal('${modelId}')">Test Connection</button>
                </div>
            `;
            
            modal.style.display = 'block';
        }
    } catch (error) {
        showToast('Error loading model details', 'error');
        console.error('Error:', error);
    }
}

// Set as default from modal
window.setAsDefaultFromModal = async function(modelId) {
    await setAsDefault(modelId);
    document.getElementById('model-modal').style.display = 'none';
};

// Test model from modal
window.testModelFromModal = async function(modelId) {
    showToast('Testing model connection...', 'success');
    
    try {
        const response = await fetch(`${API_BASE}/api/ai-models/${modelId}/test`, {
            method: 'POST'
        });
        const result = await response.json();
        
        modelStatuses[modelId] = result;
        
        if (result.available) {
            showToast('✅ Model is available and working!', 'success');
        } else {
            showToast(`⚠️ ${result.message}`, 'error');
        }
        
        // Refresh modal
        await showModelDetails(modelId);
    } catch (error) {
        showToast('Error testing model', 'error');
    }
};

// Load provider summary
async function loadProviderSummary() {
    try {
        const response = await fetch(`${API_BASE}/api/ai-models/providers/summary`);
        const data = await response.json();
        
        if (data.success) {
            displayProviderSummary(data.providers);
        }
    } catch (error) {
        console.error('Error loading provider summary:', error);
    }
}

// Display provider summary
function displayProviderSummary(providers) {
    const grid = document.getElementById('provider-summary-grid');
    
    const providerHtml = Object.entries(providers).map(([key, provider]) => `
        <div class="provider-card">
            <h3>${provider.name}</h3>
            <p>${provider.description}</p>
            <div class="provider-stats">
                <div class="stat-item">
                    <strong>${provider.model_count}</strong> models
                </div>
                <div class="stat-item">
                    API Key: <strong>${provider.requires_api_key ? 'Required' : 'Not Required'}</strong>
                </div>
                <div class="stat-item">
                    Cost: <strong>${provider.cost_model}</strong>
                </div>
            </div>
        </div>
    `).join('');
    
    grid.innerHTML = providerHtml;
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}
