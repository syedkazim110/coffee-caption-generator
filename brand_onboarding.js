// Brand Onboarding Wizard JavaScript
let currentStep = 1;
const totalSteps = 4;
let isEditMode = false;
let currentBrandId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    detectEditMode();
});

// Detect edit mode from URL parameters
function detectEditMode() {
    const urlParams = new URLSearchParams(window.location.search);
    const brandId = urlParams.get('brand_id');
    const mode = urlParams.get('mode');
    
    if (brandId && mode === 'edit') {
        isEditMode = true;
        currentBrandId = parseInt(brandId);
        document.getElementById('brandId').value = brandId;
        document.getElementById('editMode').value = 'true';
        
        // Update UI for edit mode
        updateUIForEditMode();
        
        // Load brand data
        loadBrandData(currentBrandId);
    }
}

// Update UI elements for edit mode
function updateUIForEditMode() {
    document.getElementById('pageTitle').textContent = 'Edit Brand Profile';
    document.getElementById('pageSubtitle').textContent = 'Update your brand information';
    document.getElementById('submitBtnText').textContent = 'Update Brand Profile';
    document.getElementById('submitBtnLoaderText').textContent = 'Updating...';
    
    // Update success modal
    const successModal = document.querySelector('#successModal .modal-content h2');
    if (successModal) {
        successModal.textContent = 'Brand Profile Updated!';
    }
}

// Load brand data and pre-populate form
async function loadBrandData(brandId) {
    try {
        const response = await fetch(`/api/brands/${brandId}`);
        const data = await response.json();
        
        if (data.success && data.brand) {
            populateForm(data.brand);
        } else {
            throw new Error('Failed to load brand data');
        }
    } catch (error) {
        console.error('Error loading brand data:', error);
        alert('Failed to load brand data. Redirecting to brand list...');
        window.location.href = 'brand_list.html';
    }
}

// Populate form with brand data
function populateForm(brand) {
    // Step 1: Initial Setup
    document.getElementById('brandName').value = brand.brand_name || '';
    document.getElementById('brandType').value = brand.brand_type || '';
    document.getElementById('productNature').value = brand.product_nature || '';
    document.getElementById('industry').value = brand.industry || '';
    document.getElementById('targetAudience').value = brand.target_audience || '';
    document.getElementById('contentLanguage').value = brand.content_language || 'English (US)';
    
    // Step 2: Brand Voice Profile
    if (brand.voice_profile) {
        const voiceProfile = typeof brand.voice_profile === 'string' 
            ? JSON.parse(brand.voice_profile) 
            : brand.voice_profile;
        
        // Populate adjectives
        if (voiceProfile.core_adjectives && voiceProfile.core_adjectives.length > 0) {
            const adjectivesContainer = document.getElementById('adjectivesContainer');
            adjectivesContainer.innerHTML = '';
            voiceProfile.core_adjectives.forEach(adj => {
                const div = document.createElement('div');
                div.className = 'adjective-input';
                div.innerHTML = `
                    <input type="text" class="adjective" placeholder="e.g., Bold" value="${escapeHtml(adj)}">
                    <button type="button" class="btn-remove" onclick="removeAdjective(this)">×</button>
                `;
                adjectivesContainer.appendChild(div);
            });
        }
        
        // Populate always use terms
        if (voiceProfile.lexicon_always_use && voiceProfile.lexicon_always_use.length > 0) {
            const alwaysUseContainer = document.getElementById('alwaysUseContainer');
            alwaysUseContainer.innerHTML = '';
            voiceProfile.lexicon_always_use.forEach(term => {
                const div = document.createElement('div');
                div.className = 'lexicon-input';
                div.innerHTML = `
                    <input type="text" class="always-use-term" placeholder="e.g., ethically sourced" value="${escapeHtml(term)}">
                    <button type="button" class="btn-remove" onclick="removeLexicon(this)">×</button>
                `;
                alwaysUseContainer.appendChild(div);
            });
        }
        
        // Populate never use terms
        if (voiceProfile.lexicon_never_use && voiceProfile.lexicon_never_use.length > 0) {
            const neverUseContainer = document.getElementById('neverUseContainer');
            neverUseContainer.innerHTML = '';
            voiceProfile.lexicon_never_use.forEach(term => {
                const div = document.createElement('div');
                div.className = 'lexicon-input';
                div.innerHTML = `
                    <input type="text" class="never-use-term" placeholder="e.g., cheap" value="${escapeHtml(term)}">
                    <button type="button" class="btn-remove" onclick="removeLexicon(this)">×</button>
                `;
                neverUseContainer.appendChild(div);
            });
        }
    }
    
    // Step 3: Guardrails
    if (brand.guardrails) {
        const guardrails = typeof brand.guardrails === 'string' 
            ? JSON.parse(brand.guardrails) 
            : brand.guardrails;
        
        // Set inappropriate topics checkboxes
        if (guardrails.inappropriate_topics) {
            document.querySelectorAll('#topicsContainer input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = guardrails.inappropriate_topics.includes(checkbox.value);
            });
        }
        
        document.getElementById('factCheckLevel').value = guardrails.fact_check_level || 'Medium';
        document.getElementById('imageStyle').value = guardrails.image_style || '';
        document.getElementById('disclaimers').value = guardrails.mandatory_disclaimers || '';
    }
    
    // Step 4: Strategy
    if (brand.strategy) {
        const strategy = typeof brand.strategy === 'string' 
            ? JSON.parse(brand.strategy) 
            : brand.strategy;
        
        if (strategy.content_mix) {
            document.getElementById('mixEducation').value = strategy.content_mix.education || 40;
            document.getElementById('mixEngagement').value = strategy.content_mix.engagement || 40;
            document.getElementById('mixPromotion').value = strategy.content_mix.promotion || 20;
        }
        
        document.getElementById('workflowMode').value = strategy.workflow_mode || 'Draft & Require Approval';
    }
    
    // RAG Sources
    if (brand.rag_sources) {
        const ragSources = typeof brand.rag_sources === 'string' 
            ? JSON.parse(brand.rag_sources) 
            : brand.rag_sources;
        
        if (ragSources.urls && ragSources.urls.length > 0) {
            const sourcesContainer = document.getElementById('sourcesContainer');
            sourcesContainer.innerHTML = '';
            ragSources.urls.forEach(url => {
                const input = document.createElement('input');
                input.type = 'url';
                input.className = 'rag-source';
                input.placeholder = 'https://example.com/blog';
                input.value = url;
                input.style.marginTop = '10px';
                sourcesContainer.appendChild(input);
            });
        }
    }
}

// Handle cancel button
function handleCancel() {
    if (isEditMode) {
        window.location.href = 'brand_list.html';
    } else {
        window.location.href = '/';
    }
}

// Escape HTML helper
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

// Step navigation
function nextStep() {
    if (validateStep(currentStep)) {
        if (currentStep < totalSteps) {
            document.getElementById(`step${currentStep}`).classList.remove('active');
            document.querySelector(`.step[data-step="${currentStep}"]`).classList.add('completed');
            
            currentStep++;
            
            document.getElementById(`step${currentStep}`).classList.add('active');
            document.querySelector(`.step[data-step="${currentStep}"]`).classList.add('active');
            
            updateProgressBar();
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        document.getElementById(`step${currentStep}`).classList.remove('active');
        document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove('active');
        
        currentStep--;
        
        document.getElementById(`step${currentStep}`).classList.add('active');
        document.querySelector(`.step[data-step="${currentStep}"]`).classList.remove('completed');
        
        updateProgressBar();
    }
}

function updateProgressBar() {
    const progress = (currentStep / totalSteps) * 100;
    document.getElementById('progressFill').style.width = `${progress}%`;
}

// Validation
function validateStep(step) {
    if (step === 1) {
        const brandName = document.getElementById('brandName').value;
        const brandType = document.getElementById('brandType').value;
        const productNature = document.getElementById('productNature').value;
        const industry = document.getElementById('industry').value;
        const targetAudience = document.getElementById('targetAudience').value;
        
        if (!brandName || !brandType || !productNature || !industry || !targetAudience) {
            alert('Please fill in all required fields');
            return false;
        }
    }
    return true;
}

// Dynamic input management
function addAdjective() {
    const container = document.getElementById('adjectivesContainer');
    const div = document.createElement('div');
    div.className = 'adjective-input';
    div.innerHTML = `
        <input type="text" class="adjective" placeholder="e.g., Bold">
        <button type="button" class="btn-remove" onclick="removeAdjective(this)">×</button>
    `;
    container.appendChild(div);
}

function removeAdjective(btn) {
    btn.parentElement.remove();
}

function addAlwaysUse() {
    const container = document.getElementById('alwaysUseContainer');
    const div = document.createElement('div');
    div.className = 'lexicon-input';
    div.innerHTML = `
        <input type="text" class="always-use-term" placeholder="e.g., ethically sourced">
        <button type="button" class="btn-remove" onclick="removeLexicon(this)">×</button>
    `;
    container.appendChild(div);
}

function addNeverUse() {
    const container = document.getElementById('neverUseContainer');
    const div = document.createElement('div');
    div.className = 'lexicon-input';
    div.innerHTML = `
        <input type="text" class="never-use-term" placeholder="e.g., cheap">
        <button type="button" class="btn-remove" onclick="removeLexicon(this)">×</button>
    `;
    container.appendChild(div);
}

function removeLexicon(btn) {
    btn.parentElement.remove();
}

function addSource() {
    const container = document.getElementById('sourcesContainer');
    const input = document.createElement('input');
    input.type = 'url';
    input.className = 'rag-source';
    input.placeholder = 'https://example.com/blog';
    input.style.marginTop = '10px';
    container.appendChild(input);
}

// AI Suggestions
async function generateVoiceAdjectives() {
    const brandType = document.getElementById('brandType').value;
    const productNature = document.getElementById('productNature').value;
    const industry = document.getElementById('industry').value;
    const targetAudience = document.getElementById('targetAudience').value;
    
    if (!brandType || !productNature || !industry || !targetAudience) {
        alert('Please complete Step 1 first');
        return;
    }
    
    try {
        const response = await fetch('/api/brands/suggest-voice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                brand_type: brandType,
                product_nature: productNature,
                industry: industry,
                target_audience: targetAudience
            })
        });
        
        const data = await response.json();
        displayVoiceSuggestions(data.suggestions.adjectives);
    } catch (error) {
        console.error('Error generating suggestions:', error);
        alert('Failed to generate suggestions');
    }
}

function displayVoiceSuggestions(adjectives) {
    const container = document.getElementById('aiSuggestions');
    container.innerHTML = '<h4>AI Suggested Adjectives:</h4>';
    
    adjectives.forEach(adj => {
        const div = document.createElement('div');
        div.className = 'suggestion-item';
        div.innerHTML = `
            <div class="suggestion-content">
                <div class="suggestion-term">${adj.adjective}</div>
                <div class="suggestion-reason">${adj.rationale}</div>
            </div>
            <button class="btn-use" onclick="useAdjective('${adj.adjective}')">Use</button>
        `;
        container.appendChild(div);
    });
    
    container.style.display = 'block';
}

function useAdjective(adjective) {
    const inputs = document.querySelectorAll('.adjective');
    const emptyInput = Array.from(inputs).find(input => !input.value);
    
    if (emptyInput) {
        emptyInput.value = adjective;
    } else {
        addAdjective();
        const newInputs = document.querySelectorAll('.adjective');
        newInputs[newInputs.length - 1].value = adjective;
    }
}

async function generateLexicon() {
    const productNature = document.getElementById('productNature').value;
    const industry = document.getElementById('industry').value;
    
    if (!productNature || !industry) {
        alert('Please complete Step 1 first');
        return;
    }
    
    try {
        const response = await fetch('/api/brands/suggest-lexicon', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_nature: productNature,
                industry: industry
            })
        });
        
        const data = await response.json();
        populateLexicon(data.suggestions);
    } catch (error) {
        console.error('Error generating lexicon:', error);
        alert('Failed to generate lexicon suggestions');
    }
}

function populateLexicon(suggestions) {
    // Populate always use
    const alwaysInputs = document.querySelectorAll('.always-use-term');
    suggestions.always_use.forEach((item, index) => {
        if (index < alwaysInputs.length) {
            alwaysInputs[index].value = item.term;
        }
    });
    
    // Populate never use
    const neverInputs = document.querySelectorAll('.never-use-term');
    suggestions.never_use.forEach((item, index) => {
        if (index < neverInputs.length) {
            neverInputs[index].value = item.term;
        }
    });
}

// Form submission
async function submitBrand() {
    const btn = document.getElementById('submitBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    btn.disabled = true;
    
    try {
        // Collect all data
        const brandData = {
            brand_name: document.getElementById('brandName').value,
            brand_type: document.getElementById('brandType').value,
            product_nature: document.getElementById('productNature').value,
            industry: document.getElementById('industry').value,
            target_audience: document.getElementById('targetAudience').value,
            content_language: document.getElementById('contentLanguage').value,
            
            voice_profile: {
                core_adjectives: Array.from(document.querySelectorAll('.adjective'))
                    .map(input => input.value)
                    .filter(v => v),
                lexicon_always_use: Array.from(document.querySelectorAll('.always-use-term'))
                    .map(input => input.value)
                    .filter(v => v),
                lexicon_never_use: Array.from(document.querySelectorAll('.never-use-term'))
                    .map(input => input.value)
                    .filter(v => v)
            },
            
            guardrails: {
                inappropriate_topics: Array.from(document.querySelectorAll('#topicsContainer input:checked'))
                    .map(input => input.value),
                fact_check_level: document.getElementById('factCheckLevel').value,
                image_style: document.getElementById('imageStyle').value,
                mandatory_disclaimers: document.getElementById('disclaimers').value
            },
            
            strategy: {
                content_mix: {
                    education: parseInt(document.getElementById('mixEducation').value),
                    engagement: parseInt(document.getElementById('mixEngagement').value),
                    promotion: parseInt(document.getElementById('mixPromotion').value)
                },
                workflow_mode: document.getElementById('workflowMode').value
            },
            
            rag_sources: {
                urls: Array.from(document.querySelectorAll('.rag-source'))
                    .map(input => input.value)
                    .filter(v => v)
            }
        };
        
        // Determine API endpoint and method based on mode
        let url, method, successMessage;
        if (isEditMode && currentBrandId) {
            url = `/api/brands/${currentBrandId}`;
            method = 'PUT';
            successMessage = `Brand "${brandData.brand_name}" has been updated successfully!`;
        } else {
            url = '/api/brands/create';
            method = 'POST';
            successMessage = `Your brand "${brandData.brand_name}" has been created successfully!`;
        }
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(brandData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('successMessage').textContent = successMessage;
            
            // Update success modal button based on mode
            const successButton = document.querySelector('#successModal .btn-primary');
            if (isEditMode) {
                successButton.textContent = 'Back to Brand List';
                successButton.onclick = () => window.location.href = 'brand_list.html';
            } else {
                successButton.textContent = 'Start Generating Content';
                successButton.onclick = () => window.location.href = 'index.html';
            }
            
            document.getElementById('successModal').style.display = 'flex';
        } else {
            throw new Error(data.message || `Failed to ${isEditMode ? 'update' : 'create'} brand`);
        }
    } catch (error) {
        console.error(`Error ${isEditMode ? 'updating' : 'creating'} brand:`, error);
        document.getElementById('errorMessage').textContent = error.message;
        document.getElementById('errorModal').style.display = 'flex';
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        btn.disabled = false;
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}
