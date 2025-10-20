// ===============================================
// ADMIN.JS - GESTIONARE PANOU ADMIN
// ===============================================

// Baza de date simulată pentru produse (în localStorage)
let products = JSON.parse(localStorage.getItem('products')) || [
    {
        id: 1,
        name: 'Dark Side of the Moon',
        artist: 'Pink Floyd',
        category: 'cd',
        genre: 'Rock',
        price: 49.99,
        stock: 25,
        year: 1973,
        status: 'active',
        description: 'Album legendary de rock progresiv'
    },
    {
        id: 2,
        name: 'Abbey Road',
        artist: 'The Beatles',
        category: 'vinyl',
        genre: 'Rock',
        price: 139.99,
        stock: 15,
        year: 1969,
        status: 'active',
        description: 'Unul dintre cele mai iconice albume ale Beatles'
    }
];

// Inițializare
document.addEventListener('DOMContentLoaded', function() {
    loadProducts();
    initAddProductForm();
    initSearch();
});

// ===============================================
// GESTIONARE PRODUSE
// ===============================================

function loadProducts() {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    products.forEach(product => {
        const row = createProductRow(product);
        tbody.appendChild(row);
    });
}

function createProductRow(product) {
    const tr = document.createElement('tr');
    
    const categoryIcon = {
        'cd': 'fa-compact-disc',
        'vinyl': 'fa-record-vinyl',
        'merch': 'fa-tshirt'
    };

    const categoryBadge = {
        'cd': 'badge-cd',
        'vinyl': 'badge-vinyl',
        'merch': 'badge-merch'
    };

    const categoryName = {
        'cd': 'CD',
        'vinyl': 'Vinil',
        'merch': 'Merch'
    };

    tr.innerHTML = `
        <td>#${String(product.id).padStart(3, '0')}</td>
        <td>
            <div class="product-cell">
                <i class="fas ${categoryIcon[product.category]}"></i>
                <span>${product.name} - ${product.artist}</span>
            </div>
        </td>
        <td><span class="badge ${categoryBadge[product.category]}">${categoryName[product.category]}</span></td>
        <td>${product.price.toFixed(2)} RON</td>
        <td>
            <input type="number" value="${product.stock}" class="stock-input" min="0" 
                   onchange="updateStock(${product.id}, this.value)">
        </td>
        <td><span class="status-badge ${product.status}">${product.status === 'active' ? 'Activ' : 'Inactiv'}</span></td>
        <td>
            <div class="action-buttons">
                <button class="btn-icon edit" title="Editează" onclick="editProduct(${product.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn-icon delete" title="Șterge" onclick="deleteProduct(${product.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </td>
    `;

    return tr;
}

function updateStock(productId, newStock) {
    const product = products.find(p => p.id === productId);
    if (product) {
        product.stock = parseInt(newStock);
        saveProducts();
        showNotification('Stoc actualizat cu succes!', 'success');
    }
}

function deleteProduct(productId) {
    if (confirm('Ești sigur că vrei să ștergi acest produs?')) {
        products = products.filter(p => p.id !== productId);
        saveProducts();
        loadProducts();
        showNotification('Produs șters cu succes!', 'success');
    }
}

function editProduct(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;

    // Populează formularul cu datele produsului
    document.getElementById('productName').value = product.name;
    document.getElementById('productArtist').value = product.artist;
    document.getElementById('productCategory').value = product.category;
    document.getElementById('productGenre').value = product.genre;
    document.getElementById('productPrice').value = product.price;
    document.getElementById('productStock').value = product.stock;
    document.getElementById('productYear').value = product.year;
    document.getElementById('productDescription').value = product.description || '';

    // Schimbă la tab-ul de adăugare
    document.querySelector('[data-tab="add"]').click();

    // Marchează că este în modul editare
    const form = document.getElementById('addProductForm');
    form.dataset.editId = productId;
    document.querySelector('#add-tab h2').textContent = 'Editează Produs';
}

function saveProducts() {
    localStorage.setItem('products', JSON.stringify(products));
}

// ===============================================
// FORMULAR ADĂUGARE PRODUS
// ===============================================

function initAddProductForm() {
    const form = document.getElementById('addProductForm');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();

        const formData = {
            name: document.getElementById('productName').value,
            artist: document.getElementById('productArtist').value,
            category: document.getElementById('productCategory').value,
            genre: document.getElementById('productGenre').value,
            price: parseFloat(document.getElementById('productPrice').value),
            stock: parseInt(document.getElementById('productStock').value),
            year: parseInt(document.getElementById('productYear').value) || null,
            label: document.getElementById('productLabel').value || '',
            description: document.getElementById('productDescription').value || '',
            status: 'active'
        };

        // Verifică dacă este editare sau adăugare
        const editId = form.dataset.editId;

        if (editId) {
            // Editare
            const product = products.find(p => p.id === parseInt(editId));
            if (product) {
                Object.assign(product, formData);
                showNotification('Produs actualizat cu succes!', 'success');
            }
            delete form.dataset.editId;
            document.querySelector('#add-tab h2').textContent = 'Adaugă Produs Nou';
        } else {
            // Adăugare
            const newProduct = {
                id: products.length > 0 ? Math.max(...products.map(p => p.id)) + 1 : 1,
                ...formData
            };
            products.push(newProduct);
            showNotification('Produs adăugat cu succes!', 'success');
        }

        saveProducts();
        loadProducts();
        form.reset();
        
        // Revino la tab-ul produse
        document.querySelector('[data-tab="products"]').click();
    });

    // Reset la click pe butonul de reset
    form.addEventListener('reset', function() {
        delete form.dataset.editId;
        document.querySelector('#add-tab h2').textContent = 'Adaugă Produs Nou';
    });
}

// ===============================================
// CĂUTARE ȘI FILTRARE
// ===============================================

function initSearch() {
    const searchInput = document.querySelector('.search-input');
    const filterSelect = document.querySelector('.filter-select');

    if (searchInput) {
        searchInput.addEventListener('input', function() {
            filterProducts(this.value, filterSelect ? filterSelect.value : '');
        });
    }

    if (filterSelect) {
        filterSelect.addEventListener('change', function() {
            filterProducts(searchInput ? searchInput.value : '', this.value);
        });
    }
}

function filterProducts(searchTerm, category) {
    const tbody = document.getElementById('productsTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    const filtered = products.filter(product => {
        const matchesSearch = searchTerm === '' || 
            product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            product.artist.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesCategory = category === '' || product.category === category;

        return matchesSearch && matchesCategory;
    });

    filtered.forEach(product => {
        const row = createProductRow(product);
        tbody.appendChild(row);
    });

    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 2rem;">Nu s-au găsit produse</td></tr>';
    }
}

// ===============================================
// NOTIFICĂRI
// ===============================================

function showNotification(message, type = 'success') {
    // Creează element notificare
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : '#ef4444'};
        color: white;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Elimină după 3 secunde
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Adaugă CSS pentru animații
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
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
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ===============================================
// EXPORT FUNCTIONS
// ===============================================

window.updateStock = updateStock;
window.deleteProduct = deleteProduct;
window.editProduct = editProduct;
