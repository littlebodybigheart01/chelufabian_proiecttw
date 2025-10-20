// ===============================================
// GARDEN OF RECORDS - JAVASCRIPT PRINCIPAL
// ===============================================

// Variabile globale
let cart = JSON.parse(localStorage.getItem('cart')) || [];

// Inițializare
document.addEventListener('DOMContentLoaded', function() {
    initNavigation();
    initTabs();
    updateCartDisplay();
    updateUserSection();
});

// ===============================================
// NAVIGARE
// ===============================================

function initNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    if (hamburger) {
        hamburger.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
        });
    }

    // Închide meniul la click pe link
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', () => {
            if (navMenu) navMenu.classList.remove('active');
            if (hamburger) hamburger.classList.remove('active');
        });
    });
}

// ===============================================
// USER SECTION
// ===============================================

function updateUserSection() {
    const userSection = document.getElementById('userSection');
    if (!userSection) return;

    const user = checkAuth();
    
    if (user) {
        userSection.innerHTML = `
            <div class="user-dropdown">
                <button class="user-btn" id="userMenuBtn">
                    <i class="fas fa-user-circle"></i>
                    <span>${user.name}</span>
                    <i class="fas fa-chevron-down"></i>
                </button>
                <div class="dropdown-menu" id="dropdownMenu">
                    <a href="profile.html">
                        <i class="fas fa-user"></i> Profilul Meu
                    </a>
                    <a href="comenzi.html">
                        <i class="fas fa-box"></i> Comenzile Mele
                    </a>
                    ${user.role === 'admin' ? `
                    <a href="admin.html">
                        <i class="fas fa-cog"></i> Panou Admin
                    </a>
                    ` : ''}
                    <a href="#" onclick="logout(); return false;">
                        <i class="fas fa-sign-out-alt"></i> Deconectare
                    </a>
                </div>
            </div>
        `;

        // Toggle dropdown
        const userBtn = document.getElementById('userMenuBtn');
        const dropdownMenu = document.getElementById('dropdownMenu');
        
        if (userBtn && dropdownMenu) {
            userBtn.addEventListener('click', function(e) {
                e.stopPropagation();
                dropdownMenu.classList.toggle('active');
            });

            // Închide dropdown la click în afară
            document.addEventListener('click', function() {
                dropdownMenu.classList.remove('active');
            });
        }
    } else {
        userSection.innerHTML = `
            <a href="login.html" class="btn-login-nav">
                <i class="fas fa-sign-in-alt"></i>
                <span>Login</span>
            </a>
        `;
    }
}

// ===============================================
// TABS
// ===============================================

function initTabs() {
    // Tabs pentru comenzi
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            const targetTab = document.getElementById(`${tabName}-tab`);
            if (targetTab) targetTab.classList.add('active');
        });
    });

    // Tabs pentru admin
    const adminTabButtons = document.querySelectorAll('.admin-tab-btn');
    const adminTabContents = document.querySelectorAll('.admin-tab-content');

    adminTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.dataset.tab;

            adminTabButtons.forEach(btn => btn.classList.remove('active'));
            adminTabContents.forEach(content => content.classList.remove('active'));

            button.classList.add('active');
            const targetTab = document.getElementById(`${tabName}-tab`);
            if (targetTab) targetTab.classList.add('active');
        });
    });
}

// ===============================================
// COȘ DE CUMPĂRĂTURI
// ===============================================

function addToCart(productName, price) {
    const product = {
        id: Date.now(),
        name: productName,
        price: price,
        quantity: 1
    };

    cart.push(product);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();
    
    // Notificare
    alert(`${productName} a fost adăugat în coș!`);
}

function updateCartDisplay() {
    const cartCountElements = document.querySelectorAll('.cart-count');
    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    
    cartCountElements.forEach(element => {
        element.textContent = totalItems;
    });
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();
}

function clearCart() {
    cart = [];
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();
}

// ===============================================
// UTILITY FUNCTIONS
// ===============================================

function checkAuth() {
    const authToken = localStorage.getItem('authToken');
    const currentUser = localStorage.getItem('currentUser');
    
    if (authToken && currentUser) {
        return JSON.parse(currentUser);
    }
    return null;
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('tempSession');
    window.location.href = 'index.html';
}
