// Brand List Management JavaScript
let brands = [];
let brandToDelete = null;

// Load brands on page load
document.addEventListener('DOMContentLoaded', () => {
    loadBrands();
});

// Load all brands from API
async function loadBrands() {
    try {
        const response = await fetch('/api/brands/list');
        const data = await response.json();
        
        if (data.success) {
            brands = data.brands;
            displayBrands(brands);
        } else {
            throw new Error('Failed to load brands');
        }
    } catch (error) {
        console.error('Error loading brands:', error);
        showError('Failed to load brands. Please refresh the page.');
    }
}

// Display brands in cards
function displayBrands(brandsList) {
    const container = document.getElementById('brandsContainer');
    const emptyState = document.getElementById('emptyState');
    
    if (!brandsList || brandsList.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }
    
    container.innerHTML = '';
    container.style.display = 'grid';
    emptyState.style.display = 'none';
    
    brandsList.forEach(brand => {
        const card = createBrandCard(brand);
        container.appendChild(card);
    });
}

// Create brand card HTML
function createBrandCard(brand) {
    const card = document.createElement('div');
    card.className = `brand-card ${brand.is_active ? 'active' : ''}`;
    
    const createdDate = new Date(brand.created_at).toLocaleDateString();
    
    card.innerHTML = `
        ${brand.is_active ? '<div class="active-badge">✓ Active</div>' : ''}
        
        <div class="brand-header">
            <div class="brand-icon">🏢</div>
            <div class="brand-info">
                <h3>${escapeHtml(brand.brand_name)}</h3>
                <div class="brand-type">${escapeHtml(brand.brand_type)}</div>
            </div>
        </div>
        
        <div class="brand-details">
            <div class="detail-row">
                <span class="detail-label">Industry:</span>
                <span class="detail-value">${escapeHtml(brand.industry)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Created:</span>
                <span class="detail-value">${createdDate}</span>
            </div>
        </div>
        
        <div class="brand-actions">
            <button class="btn btn-primary btn-small" onclick="editBrand(${brand.id})">
                ✏️ Edit
            </button>
            ${!brand.is_active ? `
                <button class="btn btn-success btn-small" onclick="activateBrand(${brand.id}, '${escapeHtml(brand.brand_name)}')">
                    ✓ Set Active
                </button>
            ` : ''}
            <button class="btn btn-danger btn-small" onclick="showDeleteModal(${brand.id}, '${escapeHtml(brand.brand_name)}')">
                🗑️ Delete
            </button>
        </div>
    `;
    
    return card;
}

// Edit brand - navigate to onboarding page with brand_id
function editBrand(brandId) {
    window.location.href = `brand_onboarding.html?brand_id=${brandId}&mode=edit`;
}

// Activate brand
async function activateBrand(brandId, brandName) {
    try {
        const response = await fetch(`/api/brands/${brandId}/activate`, {
            method: 'PUT'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess(`"${brandName}" is now active!`);
            // Reload brands to update UI
            await loadBrands();
        } else {
            throw new Error(data.message || 'Failed to activate brand');
        }
    } catch (error) {
        console.error('Error activating brand:', error);
        showError(error.message);
    }
}

// Show delete confirmation modal
function showDeleteModal(brandId, brandName) {
    brandToDelete = brandId;
    document.getElementById('deleteMessage').textContent = 
        `Are you sure you want to delete "${brandName}"?`;
    document.getElementById('deleteModal').style.display = 'flex';
}

// Close delete modal
function closeDeleteModal() {
    brandToDelete = null;
    document.getElementById('deleteModal').style.display = 'none';
}

// Confirm delete
async function confirmDelete() {
    if (!brandToDelete) return;
    
    const btn = document.getElementById('confirmDeleteBtn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline-flex';
    btn.disabled = true;
    
    try {
        const response = await fetch(`/api/brands/${brandToDelete}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeDeleteModal();
            showSuccess('Brand deleted successfully!');
            // Reload brands
            await loadBrands();
        } else {
            throw new Error(data.message || 'Failed to delete brand');
        }
    } catch (error) {
        console.error('Error deleting brand:', error);
        showError(error.message);
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        btn.disabled = false;
    }
}

// Show success modal
function showSuccess(message) {
    document.getElementById('successMessage').textContent = message;
    document.getElementById('successModal').style.display = 'flex';
}

// Close success modal
function closeSuccessModal() {
    document.getElementById('successModal').style.display = 'none';
}

// Show error modal
function showError(message) {
    document.getElementById('errorMessage').textContent = message;
    document.getElementById('errorModal').style.display = 'flex';
}

// Close error modal
function closeErrorModal() {
    document.getElementById('errorModal').style.display = 'none';
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}
