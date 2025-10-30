// Global variable to store current post data
let currentPostData = null;
let selectedPlatform = 'instagram'; // Default platform
let availableModels = {};

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
    loadBrands();
    loadAIModels();
    setupEventListeners();
    setupPlatformButtons();
    
    // Setup OAuth message listener for popup callback
    window.addEventListener('message', handleOAuthMessage);
    
    // Check connection status on load
    checkAllConnectionStatus();
});

// Load available AI models
async function loadAIModels() {
    try {
        const response = await fetch('/api/ai-models/list');
        const data = await response.json();
        
        if (data.success) {
            availableModels = data.models;
            const modelSelect = document.getElementById('modelSelect');
            
            // Clear existing options except default
            modelSelect.innerHTML = '<option value="">Use Default Model</option>';
            
            // Add available models
            Object.entries(data.models).forEach(([modelId, model]) => {
                const option = document.createElement('option');
                option.value = modelId;
                
                // Show model name and provider
                let displayText = `${model.display_name} (${model.provider})`;
                
                // Add cost indicator
                if (model.capabilities.cost_per_1m_tokens === 0) {
                    displayText += ' - Free';
                } else {
                    displayText += ` - $${model.capabilities.cost_per_1m_tokens}/1M`;
                }
                
                option.textContent = displayText;
                
                // Mark as default if it's the default model
                if (modelId === data.default_model) {
                    option.textContent += ' ⭐';
                }
                
                modelSelect.appendChild(option);
            });
            
            console.log(`Loaded ${Object.keys(data.models).length} AI models`);
        }
    } catch (error) {
        console.error('Error loading AI models:', error);
    }
}

// Load brands from API
async function loadBrands() {
    try {
        const response = await fetch('/api/brands/list');
        const data = await response.json();
        
        const brandSelect = document.getElementById('brandSelect');
        if (data.success && data.brands && data.brands.length > 0) {
            brandSelect.innerHTML = '<option value="">Use Active Brand</option>';
            
            data.brands.forEach(brand => {
                const option = document.createElement('option');
                option.value = brand.id;
                option.textContent = `${brand.brand_name}${brand.is_active ? ' (Active)' : ''}`;
                if (brand.is_active) {
                    option.selected = true;
                }
                brandSelect.appendChild(option);
            });
        } else {
            brandSelect.innerHTML = '<option value="">No brands available - Create one first</option>';
        }
    } catch (error) {
        console.error('Error loading brands:', error);
        const brandSelect = document.getElementById('brandSelect');
        brandSelect.innerHTML = '<option value="">Error loading brands</option>';
    }
}

// Setup event listeners
function setupEventListeners() {
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.addEventListener('click', generatePost);
}

// Setup platform button listeners
function setupPlatformButtons() {
    const platformButtons = document.querySelectorAll('.platform-btn');
    
    platformButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            platformButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            // Update selected platform
            selectedPlatform = button.getAttribute('data-platform');
            
            console.log(`Platform selected: ${selectedPlatform}`);
        });
    });
}

// Load statistics from API
async function loadStatistics() {
    try {
        const response = await fetch('/statistics');
        const stats = response.json();
        
        stats.then(data => {
            const statsElement = document.getElementById('statistics');
            statsElement.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; text-align: left;">
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">Total Documents</div>
                        <div style="font-size: 18px; font-weight: 600;">${data.total_documents}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">Trending Keywords</div>
                        <div style="font-size: 18px; font-weight: 600;">${data.trending_keywords}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">Hashtag Knowledge</div>
                        <div style="font-size: 18px; font-weight: 600;">${data.hashtag_knowledge}</div>
                    </div>
                    <div>
                        <div style="font-size: 11px; opacity: 0.8; margin-bottom: 3px;">LLM Model</div>
                        <div style="font-size: 14px; font-weight: 600;">${data.llm_model || 'N/A'}</div>
                    </div>
                </div>
            `;
        });
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Generate post
async function generatePost() {
    const generateBtn = document.getElementById('generateBtn');
    const btnText = generateBtn.querySelector('.btn-text');
    const btnLoader = generateBtn.querySelector('.btn-loader');
    const postContainer = document.getElementById('postContainer');
    const errorContainer = document.getElementById('errorContainer');
    
    // Hide previous results
    postContainer.style.display = 'none';
    errorContainer.style.display = 'none';
    
    // Show loading state
    generateBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    
    try {
        // Get selected brand ID
        const brandSelect = document.getElementById('brandSelect');
        const brandId = brandSelect.value ? parseInt(brandSelect.value) : null;
        
        // Get scenario input (optional)
        const scenarioInput = document.getElementById('scenarioInput');
        const scenario = scenarioInput.value.trim() || null;
        
        // Get keyword input (optional)
        const keywordInput = document.getElementById('keywordInput');
        const keyword = keywordInput.value.trim() || null;
        
        // Get selected model (if any)
        const modelSelect = document.getElementById('modelSelect');
        const selectedModel = modelSelect.value || null;
        
        const response = await fetch('/generate-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: keyword, // Use provided keyword or null for random
                brand_id: brandId,
                platform: selectedPlatform,
                scenario: scenario,
                model_id: selectedModel
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentPostData = data;
        console.log('Generated Post Data:', data);
        // Display the post
        displayPost(data);
        
        // Scroll to post
        setTimeout(() => {
            postContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
        
    } catch (error) {
        console.error('Error generating post:', error);
        showError(error.message);
    } finally {
        // Reset button state
        generateBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Display post
function displayPost(data) {
    const postContainer = document.getElementById('postContainer');
    const imageContainer = document.getElementById('imageContainer');
    
    // Log the received data for debugging
    console.log('Display Post - Platform received:', data.platform);
    console.log('Display Post - Selected platform:', selectedPlatform);
    
    // Update caption
    document.getElementById('captionText').textContent = data.caption;
    
    // Update hashtags
    document.getElementById('hashtagsText').textContent = data.hashtags.join(' ');
    
    // Update metadata - use the platform from response data
    const platformDisplay = (data.platform || selectedPlatform || 'instagram').toUpperCase();
    console.log('Displaying platform as:', platformDisplay);
    document.getElementById('platformText').textContent = platformDisplay;
    document.getElementById('keywordText').textContent = data.keyword;
    document.getElementById('visualStyleText').textContent = data.visual_style;
    document.getElementById('imagePromptText').textContent = data.image_prompt;
    document.getElementById('methodText').textContent = data.generation_method;
    
    // Update timestamp
    const timestamp = new Date(data.timestamp);
    document.getElementById('postTime').textContent = formatTimestamp(timestamp);
    
    // Handle image
    if (data.image_base64) {
        imageContainer.innerHTML = `
            <img src="data:image/png;base64,${data.image_base64}" alt="Generated coffee image">
        `;
    } else {
        imageContainer.innerHTML = `
            <div class="placeholder-image">
                <span class="placeholder-icon">🖼️</span>
                <p>Image prompt generated successfully</p>
                <p class="placeholder-subtitle">Use the prompt below with any image generation tool</p>
            </div>
        `;
    }
    
    // Store context_snippets for regeneration (important for RAG consistency)
    if (data.context_snippets && data.context_snippets.length > 0) {
        currentPostData.context_snippets = data.context_snippets;
        console.log(`Stored ${data.context_snippets.length} context snippets for regeneration`);
    }
    
    // Show post
    postContainer.style.display = 'block';
}

// Show error
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message || 'An unexpected error occurred. Please try again.';
    errorContainer.style.display = 'block';
    
    // Scroll to error
    setTimeout(() => {
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
}

// Format timestamp
function formatTimestamp(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
}

// Copy caption to clipboard
function copyToClipboard() {
    if (!currentPostData) return;
    
    const textToCopy = currentPostData.full_caption;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Caption copied to clipboard! ✅');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy caption ❌');
    });
}

// Copy image prompt to clipboard
function copyImagePrompt() {
    if (!currentPostData) return;
    
    const textToCopy = currentPostData.image_prompt;
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        showNotification('Image prompt copied to clipboard! ✅');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showNotification('Failed to copy image prompt ❌');
    });
}

// Download post as JSON
function downloadPost() {
    if (!currentPostData) return;
    
    const dataStr = JSON.stringify(currentPostData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `coffee_post_${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Post data downloaded! 💾');
}

// Regenerate image with new prompt
async function regenerateImage() {
    if (!currentPostData) {
        showNotification('No post available to regenerate ❌');
        return;
    }
    
    const regenerateBtn = document.getElementById('regenerateImageBtn');
    const btnText = regenerateBtn.querySelector('.btn-text');
    const btnLoader = regenerateBtn.querySelector('.btn-loader');
    const imageContainer = document.getElementById('imageContainer');
    
    // Show loading state
    regenerateBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    
    try {
        const response = await fetch('/regenerate-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                keyword: currentPostData.keyword,
                caption: currentPostData.caption,
                context_snippets: currentPostData.context_snippets || []  // Send RAG context
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Regenerated image data:', data);
        
        // Update current post data with new values
        currentPostData.image_prompt = data.image_prompt;
        currentPostData.image_base64 = data.image_base64;
        currentPostData.visual_style = data.visual_style;
        
        // Update image display
        if (data.image_base64) {
            imageContainer.innerHTML = `
                <img src="data:image/png;base64,${data.image_base64}" alt="Generated coffee image">
            `;
        } else {
            imageContainer.innerHTML = `
                <div class="placeholder-image">
                    <span class="placeholder-icon">🖼️</span>
                    <p>New image prompt generated</p>
                    <p class="placeholder-subtitle">Use the prompt below with any image generation tool</p>
                </div>
            `;
        }
        
        // Update metadata display
        document.getElementById('imagePromptText').textContent = data.image_prompt;
        document.getElementById('visualStyleText').textContent = data.visual_style;
        
        // Show success notification
        showNotification('Image regenerated successfully! 🎨');
        
    } catch (error) {
        console.error('Error regenerating image:', error);
        showNotification('Failed to regenerate image ❌');
    } finally {
        // Reset button state
        regenerateBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// ========================================
// SOCIAL MEDIA OAUTH & PUBLISHING
// ========================================

// Store OAuth popup reference
let oauthPopup = null;

// Check all platform connection status
async function checkAllConnectionStatus() {
    await checkConnectionStatus('instagram');
    await checkConnectionStatus('facebook');
    await checkConnectionStatus('twitter');
}

// Check connection status for a platform
async function checkConnectionStatus(platform) {
    try {
        // Get brand ID
        const brandSelect = document.getElementById('brandSelect');
        const brandId = brandSelect.value ? parseInt(brandSelect.value) : 1; // Default to 1 if no brand selected
        
        const response = await fetch(`/api/social/status?platform=${platform}&brand_id=${brandId}`);
        const data = await response.json();
        
        updatePlatformUI(platform, data);
    } catch (error) {
        console.error(`Error checking ${platform} status:`, error);
    }
}

// Update platform UI based on connection status
function updatePlatformUI(platform, statusData) {
    const statusElement = document.getElementById(`${platform}Status`);
    const accountElement = document.getElementById(`${platform}Account`);
    const accountNameElement = document.getElementById(`${platform}AccountName`);
    const checkboxElement = document.getElementById(`${platform}Check`);
    const connectBtn = document.getElementById(`${platform}ConnectBtn`);
    
    if (statusData.connected) {
        // Connected state
        statusElement.classList.remove('disconnected');
        statusElement.classList.add('connected');
        statusElement.querySelector('.status-text').textContent = 'Connected';
        
        // Show account info
        if (statusData.account) {
            accountNameElement.textContent = statusData.account;
            accountElement.style.display = 'block';
        }
        
        // Enable checkbox
        checkboxElement.disabled = false;
        
        // Update button
        connectBtn.textContent = '✓ Connected';
        connectBtn.classList.add('connected');
        connectBtn.onclick = () => disconnectPlatform(platform);
        
    } else {
        // Disconnected state
        statusElement.classList.remove('connected');
        statusElement.classList.add('disconnected');
        statusElement.querySelector('.status-text').textContent = 'Not Connected';
        
        // Hide account info
        accountElement.style.display = 'none';
        
        // Disable checkbox and uncheck
        checkboxElement.disabled = true;
        checkboxElement.checked = false;
        
        // Update button
        connectBtn.textContent = `Connect ${platform.charAt(0).toUpperCase() + platform.slice(1)}`;
        connectBtn.classList.remove('connected');
        connectBtn.onclick = () => connectPlatform(platform);
    }
    
    // Update publish button state
    updatePublishButtonState();
}

// Update publish button state based on checkboxes
function updatePublishButtonState() {
    const instagramCheck = document.getElementById('instagramCheck');
    const facebookCheck = document.getElementById('facebookCheck');
    const twitterCheck = document.getElementById('twitterCheck');
    const publishBtn = document.getElementById('publishBtn');
    
    const anyChecked = instagramCheck.checked || facebookCheck.checked || twitterCheck.checked;
    publishBtn.disabled = !anyChecked;
}

// Setup checkbox listeners
document.addEventListener('DOMContentLoaded', () => {
    const instagramCheck = document.getElementById('instagramCheck');
    const facebookCheck = document.getElementById('facebookCheck');
    const twitterCheck = document.getElementById('twitterCheck');
    
    if (instagramCheck) {
        instagramCheck.addEventListener('change', updatePublishButtonState);
    }
    if (facebookCheck) {
        facebookCheck.addEventListener('change', updatePublishButtonState);
    }
    if (twitterCheck) {
        twitterCheck.addEventListener('change', updatePublishButtonState);
    }
});

// Connect to a platform (opens OAuth popup)
async function connectPlatform(platform) {
    try {
        // Get brand ID
        const brandSelect = document.getElementById('brandSelect');
        const brandId = brandSelect.value ? parseInt(brandSelect.value) : 1;
        
        // Get OAuth URL from backend
        const response = await fetch(`/api/social/connect/${platform}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ brand_id: brandId })
        });
        
        const data = await response.json();
        
        if (data.success && data.authorization_url) {
            // Open OAuth popup
            const width = 600;
            const height = 700;
            const left = (screen.width / 2) - (width / 2);
            const top = (screen.height / 2) - (height / 2);
            
            oauthPopup = window.open(
                data.authorization_url,
                `${platform}OAuth`,
                `width=${width},height=${height},top=${top},left=${left}`
            );
            
            // Check if popup was blocked
            if (!oauthPopup || oauthPopup.closed || typeof oauthPopup.closed === 'undefined') {
                showNotification('❌ Popup blocked! Please allow popups for this site.');
            } else {
                showNotification(`Opening ${platform} authorization...`);
            }
        } else {
            showNotification(`❌ Failed to initiate ${platform} connection`);
        }
    } catch (error) {
        console.error(`Error connecting to ${platform}:`, error);
        showNotification(`❌ Error connecting to ${platform}`);
    }
}

// Handle OAuth callback message from popup
function handleOAuthMessage(event) {
    // Verify message origin for security
    const allowedOrigins = [window.location.origin, 'http://localhost:8000', 'http://localhost:8001'];
    
    if (!allowedOrigins.includes(event.origin)) {
        return;
    }
    
    const data = event.data;
    
    if (data.type === 'oauth_success') {
        showNotification(`✅ Successfully connected to ${data.platform}!`);
        
        // Refresh connection status
        checkConnectionStatus(data.platform);
        
        // Close popup if still open
        if (oauthPopup && !oauthPopup.closed) {
            oauthPopup.close();
        }
    } else if (data.type === 'oauth_error') {
        showNotification(`❌ Failed to connect to ${data.platform}: ${data.error}`);
        
        // Close popup if still open
        if (oauthPopup && !oauthPopup.closed) {
            oauthPopup.close();
        }
    }
}

// Disconnect from a platform
async function disconnectPlatform(platform) {
    if (!confirm(`Are you sure you want to disconnect from ${platform}?`)) {
        return;
    }
    
    try {
        // Get brand ID
        const brandSelect = document.getElementById('brandSelect');
        const brandId = brandSelect.value ? parseInt(brandSelect.value) : 1;
        
        const response = await fetch(`/api/social/disconnect/${platform}?brand_id=${brandId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(`✅ Disconnected from ${platform}`);
            checkConnectionStatus(platform);
        } else {
            showNotification(`❌ Failed to disconnect from ${platform}`);
        }
    } catch (error) {
        console.error(`Error disconnecting from ${platform}:`, error);
        showNotification(`❌ Error disconnecting from ${platform}`);
    }
}

// Publish to social media
async function publishToSocialMedia() {
    if (!currentPostData) {
        showNotification('❌ No post to publish. Generate a post first!');
        return;
    }
    
    const instagramCheck = document.getElementById('instagramCheck');
    const facebookCheck = document.getElementById('facebookCheck');
    const twitterCheck = document.getElementById('twitterCheck');
    const publishBtn = document.getElementById('publishBtn');
    const btnText = publishBtn.querySelector('.btn-text');
    const btnLoader = publishBtn.querySelector('.btn-loader');
    const publishResult = document.getElementById('publishResult');
    
    // Get selected platforms
    const platforms = [];
    if (instagramCheck.checked) platforms.push('instagram');
    if (facebookCheck.checked) platforms.push('facebook');
    if (twitterCheck.checked) platforms.push('twitter');
    
    if (platforms.length === 0) {
        showNotification('❌ Please select at least one platform');
        return;
    }
    
    // Show loading state
    publishBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    publishResult.style.display = 'none';
    
    try {
        // Get brand ID
        const brandSelect = document.getElementById('brandSelect');
        const brandId = brandSelect.value ? parseInt(brandSelect.value) : 1;
        
        const response = await fetch('/api/social/publish', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                brand_id: brandId,
                caption: currentPostData.caption,
                hashtags: currentPostData.hashtags,
                image_url: currentPostData.image_base64 ? `data:image/png;base64,${currentPostData.image_base64}` : null,
                platforms: platforms
            })
        });
        
        const data = await response.json();
        
        // Display results
        displayPublishResults(data);
        
    } catch (error) {
        console.error('Error publishing:', error);
        publishResult.innerHTML = `
            <h4>❌ Publishing Failed</h4>
            <p>${error.message}</p>
        `;
        publishResult.className = 'publish-result error';
        publishResult.style.display = 'block';
    } finally {
        // Reset button state
        publishBtn.disabled = false;
        btnText.style.display = 'inline-flex';
        btnLoader.style.display = 'none';
        
        // Update publish button state
        updatePublishButtonState();
    }
}

// Display publishing results
function displayPublishResults(data) {
    const publishResult = document.getElementById('publishResult');
    const results = data.results || {};
    
    let successCount = 0;
    let failCount = 0;
    let resultHTML = '<ul>';
    
    for (const [platform, result] of Object.entries(results)) {
        if (result.success) {
            successCount++;
            const postUrl = result.url || '#';
            resultHTML += `
                <li>
                    <span class="platform-result-icon success-icon">✅</span>
                    <span><strong>${platform.charAt(0).toUpperCase() + platform.slice(1)}:</strong> 
                    Published successfully! 
                    ${result.url ? `<a href="${postUrl}" target="_blank">View Post</a>` : ''}
                    </span>
                </li>
            `;
        } else {
            failCount++;
            resultHTML += `
                <li>
                    <span class="platform-result-icon error-icon">❌</span>
                    <span><strong>${platform.charAt(0).toUpperCase() + platform.slice(1)}:</strong> 
                    ${result.error || 'Failed to publish'}
                    </span>
                </li>
            `;
        }
    }
    
    resultHTML += '</ul>';
    
    // Determine overall result
    let resultClass = 'error';
    let title = '❌ Publishing Failed';
    
    if (successCount > 0 && failCount === 0) {
        resultClass = 'success';
        title = '✅ Published Successfully!';
        showNotification('✅ Post published successfully!');
    } else if (successCount > 0 && failCount > 0) {
        resultClass = 'partial';
        title = '⚠️ Partially Published';
        showNotification('⚠️ Post published to some platforms');
    } else {
        showNotification('❌ Failed to publish post');
    }
    
    publishResult.innerHTML = `<h4>${title}</h4>${resultHTML}`;
    publishResult.className = `publish-result ${resultClass}`;
    publishResult.style.display = 'block';
}

// Show notification
function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #6f4e37;
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        z-index: 1000;
        animation: slideIn 0.3s ease;
        font-weight: 500;
    `;
    notification.textContent = message;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
            document.head.removeChild(style);
        }, 300);
    }, 3000);
}
