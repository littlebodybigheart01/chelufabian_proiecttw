

// Utilizatori stocați cu parole criptate SHA-256
const USERS = {
    // Username: admin, Password: admin
    // SHA-256 hash pentru "admin" = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
    'admin': {
        username: 'admin',
        passwordHash: '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
        name: 'Administrator',
        email: 'admin@gofr.ro',
        role: 'admin'
    }
};

// Funcție pentru criptarea parolei cu SHA-256
async function hashPassword(password) {
    const msgBuffer = new TextEncoder().encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
}

// Verifică dacă utilizatorul este deja autentificat
function checkAuth() {
    const authToken = localStorage.getItem('authToken');
    const currentUser = localStorage.getItem('currentUser');
    
    if (authToken && currentUser) {
        return JSON.parse(currentUser);
    }
    return null;
}

// Salvează sesiunea utilizatorului
function saveSession(user, rememberMe) {
    const authToken = btoa(JSON.stringify({
        username: user.username,
        timestamp: Date.now(),
        rememberMe: rememberMe
    }));
    
    localStorage.setItem('authToken', authToken);
    localStorage.setItem('currentUser', JSON.stringify({
        username: user.username,
        name: user.name,
        email: user.email,
        role: user.role
    }));
    
    // Dacă nu este bifat "remember me", șterge sesiunea la închiderea browser-ului
    if (!rememberMe) {
        sessionStorage.setItem('tempSession', 'true');
    }
}

// Logout
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    sessionStorage.removeItem('tempSession');
    window.location.href = 'login.html';
}

// Afișează mesaj de eroare
function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    
    if (errorDiv && errorText) {
        errorText.textContent = message;
        errorDiv.style.display = 'flex';
        
        // Ascunde mesajul după 5 secunde
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);
    }
}

// Ascunde mesaj de eroare
function hideError() {
    const errorDiv = document.getElementById('errorMessage');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Inițializare pagină login
document.addEventListener('DOMContentLoaded', function() {
    // Verifică dacă utilizatorul este deja autentificat
    const user = checkAuth();
    if (user && window.location.pathname.includes('login.html')) {
        window.location.href = 'index.html';
        return;
    }
    
    // Toggle vizibilitate parolă
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.type === 'password' ? 'text' : 'password';
            passwordInput.type = type;
            
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
            }
        });
    }
    
    // Ascunde eroarea la editarea input-urilor
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', hideError);
    });
    
    // Form submit
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

// Procesare login
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const rememberMe = document.getElementById('rememberMe').checked;
    
    // Validare
    if (!username || !password) {
        showError('Te rugăm să completezi toate câmpurile!');
        return;
    }
    
    // Show loading
    const btnText = document.querySelector('.btn-text');
    const btnLoading = document.querySelector('.btn-loading');
    const submitBtn = document.querySelector('.btn-login');
    
    if (btnText && btnLoading && submitBtn) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'flex';
        submitBtn.disabled = true;
    }
    
    try {
        // Simulează delay pentru a face experiența mai realistă
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Criptează parola introdusă
        const hashedPassword = await hashPassword(password);
        
        // Verifică credențialele
        const user = USERS[username];
        
        if (!user || user.passwordHash !== hashedPassword) {
            showError('Nume de utilizator sau parolă incorectă!');
            
            // Reset loading
            if (btnText && btnLoading && submitBtn) {
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
                submitBtn.disabled = false;
            }
            return;
        }
        
        // Login reușit
        saveSession(user, rememberMe);
        
        // Redirect la pagina principală
        window.location.href = 'index.html';
        
    } catch (error) {
        console.error('Eroare la autentificare:', error);
        showError('A apărut o eroare. Te rugăm să încerci din nou!');
        
        // Reset loading
        if (btnText && btnLoading && submitBtn) {
            btnText.style.display = 'inline';
            btnLoading.style.display = 'none';
            submitBtn.disabled = false;
        }
    }
}

// Protejează paginile care necesită autentificare
function requireAuth() {
    const user = checkAuth();
    if (!user) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Actualizează navbar-ul pentru a afișa utilizatorul logat
function updateNavbarForLoggedUser() {
    const user = checkAuth();
    const cartIcon = document.querySelector('.cart-icon');
    
    if (user && cartIcon) {
        const userMenu = document.createElement('div');
        userMenu.className = 'user-menu';
        userMenu.innerHTML = `
            <div class="user-dropdown">
                <button class="user-btn">
                    <i class="fas fa-user-circle"></i>
                    <span>${user.name}</span>
                    <i class="fas fa-chevron-down"></i>
                </button>
                <div class="dropdown-menu">
                    <a href="comenzi.html"><i class="fas fa-box"></i> Comenzile Mele</a>
                    <a href="profile.html"><i class="fas fa-user"></i> Profilul Meu</a>
                    <a href="#" onclick="logout(); return false;"><i class="fas fa-sign-out-alt"></i> Deconectare</a>
                </div>
            </div>
        `;
        cartIcon.parentNode.insertBefore(userMenu, cartIcon);
        
        // Toggle dropdown
        const userBtn = userMenu.querySelector('.user-btn');
        const dropdownMenu = userMenu.querySelector('.dropdown-menu');
        
        userBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            dropdownMenu.classList.toggle('active');
        });
        
        // Închide dropdown la click în afară
        document.addEventListener('click', function() {
            dropdownMenu.classList.remove('active');
        });
    }
}

// Exportă funcțiile pentru a fi folosite în alte fișiere
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkAuth,
        logout,
        requireAuth,
        updateNavbarForLoggedUser
    };
}
