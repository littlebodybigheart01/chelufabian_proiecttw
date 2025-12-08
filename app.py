from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product
import os
from dotenv import load_dotenv
# AICI ERA PROBLEMA: Lipsea importul 'or_'
from sqlalchemy import desc, asc, or_

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///garden_records.db')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def initialize_session():
    if 'cart' not in session:
        session['cart'] = []

with app.app_context():
    db.create_all()

    # Check if admin exists, create if not
    if User.query.count() == 0:
        # 1. ADMIN
        admin = User(username='admin', email='admin@music.com', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # 2. ANGAJAT 
        employee = User(username='angajat', email='angajat@music.com', role='angajat')
        employee.set_password('angajat123')
        db.session.add(employee)

        # 3. CLIENT
        client = User(username='client', email='client@gmail.com', role='client')
        client.set_password('client123')
        db.session.add(client)
        
        # Add demo products (doar daca vrei sa le recreezi, poti lasa asta comentat daca ai deja produse)
        # ... codul tau pentru produse demo ...
        db.session.commit()

# ===== PUBLIC ROUTES =====

@app.route('/')
def index():
    products = Product.query.limit(6).all()
    return render_template('index.html', products=products)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Mulțumim pentru mesaj! Te vom contacta în curând.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/catalog')
def catalog():
    # 1. Preluăm parametrii
    search_query = request.args.get('q')
    category = request.args.get('category')
    artist = request.args.get('artist')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    sort_by = request.args.get('sort')
    
    page = request.args.get('page', 1, type=int)

    # 2. Query de bază
    query = Product.query

    # --- LOGICA DE CĂUTARE ---
    if search_query:
        terms = search_query.split()
        for term in terms:
            term_pattern = f"%{term}%"
            # Cautam in titlu, artist SAU descriere
            query = query.filter(or_(
                Product.title.ilike(term_pattern),
                Product.artist.ilike(term_pattern),
                Product.description.ilike(term_pattern)
            ))

    # 3. Filtre existente
    if category and category != "":
        query = query.filter(Product.category == category)
    
    if artist:
        query = query.filter(Product.artist.ilike(f'%{artist}%'))
    
    if min_price and min_price.isdigit():
        query = query.filter(Product.price >= float(min_price))
    
    if max_price and max_price.isdigit():
        query = query.filter(Product.price <= float(max_price))

    # 4. Sortare
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'name_asc':
        query = query.order_by(Product.title.asc())
    else:
        query = query.order_by(Product.id.desc())

    # 5. Paginare
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    products = pagination.items

    return render_template('catalog.html', products=products, pagination=pagination, values=request.args)

# ===== AUTH ROUTES =====

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Utilizatorul deja există', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Contul creat cu succes! Autentifică-te acum.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Bine ai venit, {username}!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Utilizator sau parolă greșit', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Te-ai deconectat cu succes', 'success')
    return redirect(url_for('index'))

# ===== DASHBOARD ROUTES =====

@app.route('/dashboard')
@login_required
def dashboard():
    stats = {}
    
    # --- STATISTICI PENTRU ADMIN ---
    if current_user.role == 'admin':
        # 1. Total Useri
        stats['total_users'] = User.query.count()
        
        # 2. Total Produse
        stats['total_products'] = Product.query.count()
        
        # 3. Produse cu stoc critic (< 5)
        stats['low_stock'] = Product.query.filter(Product.stock < 5).count()
        
        # 4. Valoare totală stoc (Opțional)
        # stats['inventory_value'] = db.session.query(db.func.sum(Product.price * Product.stock)).scalar() or 0

    # --- STATISTICI PENTRU ANGAJAT ---
    elif current_user.role == 'angajat':
        # Produse care necesită atenție (stoc 0)
        stats['out_of_stock'] = Product.query.filter(Product.stock == 0).count()

    return render_template('dashboard.html', user=current_user, stats=stats)

@app.route('/dashboard/orders')
@login_required
def my_orders():
    if current_user.role != 'client':
        return redirect(url_for('dashboard'))
    return render_template('dashboard/orders.html')

@app.route('/dashboard/settings')
@login_required
def settings():
    if current_user.role != 'client':
        return redirect(url_for('dashboard'))
    return render_template('dashboard/settings.html', user=current_user)

@app.route('/dashboard/process-orders')
@login_required
def process_orders():
    if current_user.role != 'angajat':
        flash('Acces interzis', 'error')
        return redirect(url_for('dashboard'))
    return render_template('dashboard/process_orders.html')

@app.route('/dashboard/inventory')
@login_required
def inventory():
    # 1. Verificare permisiuni
    if current_user.role not in ['angajat', 'admin']:
        flash('Acces interzis', 'error')
        return redirect(url_for('dashboard'))

    # 2. Preluare parametri
    search_query = request.args.get('q')
    category_filter = request.args.get('category')
    stock_filter = request.args.get('stock_status') # Filtru nou: Epuizat/Limitat

    # 3. Construire Query
    query = Product.query

    # --- CĂUTARE ---
    if search_query:
        term = f"%{search_query}%"
        query = query.filter(or_(
            Product.title.ilike(term),
            Product.artist.ilike(term),
            # Putem căuta și după ID dacă scrie un număr
            # (necesită cast la string în DB, dar lăsăm simplu pe text momentan)
        ))

    # --- FILTRE ---
    if category_filter and category_filter != "":
        query = query.filter(Product.category == category_filter)

    if stock_filter:
        if stock_filter == 'out':     # Stoc 0
            query = query.filter(Product.stock == 0)
        elif stock_filter == 'low':   # Stoc sub 5
            query = query.filter(Product.stock < 5, Product.stock > 0)
        elif stock_filter == 'ok':    # Stoc bun (5+)
            query = query.filter(Product.stock >= 5)

    # 4. Sortare implicită (cele mai noi sau cele cu stoc mic primele)
    # Putem pune produsele cu stoc 0 primele ca să fie observate
    query = query.order_by(Product.stock.asc(), Product.id.desc())

    products = query.all()

    return render_template('dashboard/inventory.html', products=products, values=request.args)

@app.route('/dashboard/users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        flash('Acces interzis', 'error')
        return redirect(url_for('dashboard'))
    users = User.query.all()
    return render_template('dashboard/manage_users.html', users=users)

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    # 1. Securitate
    if current_user.role not in ['angajat', 'admin']:
        flash('Acces interzis! Doar angajații și adminii pot adăuga produse.', 'error')
        return redirect(url_for('dashboard')), 403
    
    if request.method == 'POST':
        title = request.form.get('title')
        artist = request.form.get('artist')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')
        image_url = request.form.get('image_url')
        description = request.form.get('description')  # <--- Preluăm descrierea
        
        try:
            product = Product(
                title=title,
                artist=artist,
                price=float(price),
                stock=int(stock),
                category=category,
                image_url=image_url,
                description=description  # <--- O salvăm
            )
            db.session.add(product)
            db.session.commit()
            flash('Produsul a fost adăugat cu succes!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            flash(f'Eroare: {str(e)}', 'error')
            return redirect(url_for('add_product'))
    
    return render_template('add_product.html')

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    # 1. Securitate
    if current_user.role not in ['angajat', 'admin']:
        flash('Acces interzis! Nu ai permisiunea de a șterge produse.', 'error')
        return redirect(url_for('inventory'))

    # 2. Căutăm produsul
    product = Product.query.get_or_404(product_id)
    
    # 3. Ștergem produsul
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Produsul "{product.title}" a fost șters din catalog.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Eroare la ștergere: {str(e)}', 'error')

    return redirect(url_for('inventory'))

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    # 1. Securitate
    if current_user.role not in ['angajat', 'admin']:
        flash('Acces interzis!', 'error')
        return redirect(url_for('inventory'))

    product = Product.query.get_or_404(product_id)

    # 2. Salvare modificări
    if request.method == 'POST':
        try:
            product.title = request.form.get('title')
            product.artist = request.form.get('artist')
            product.price = float(request.form.get('price'))
            product.stock = int(request.form.get('stock'))
            product.category = request.form.get('category')
            product.image_url = request.form.get('image_url')
            product.description = request.form.get('description')  # <--- Actualizăm descrierea

            db.session.commit()
            flash('Produsul a fost actualizat!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Eroare la actualizare: {str(e)}', 'error')

    # Asigură-te că path-ul este corect (dashboard/...)
    return render_template('dashboard/edit_product.html', product=product)

# ===== USER MANAGEMENT =====

@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    if current_user.role != 'admin':
        flash('Acces interzis!', 'error')
        return redirect(url_for('dashboard'))

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if User.query.filter_by(username=username).first():
        flash('Utilizatorul există deja.', 'error')
        return redirect(url_for('manage_users'))
    
    try:
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Utilizatorul {username} a fost creat!', 'success')
    except Exception as e:
        flash(f'Eroare: {str(e)}', 'error')

    return redirect(url_for('manage_users'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    
    if current_user.role == 'client':
        if current_user.id != user_id:
            return jsonify({'error': 'Forbidden'}), 403
        db.session.delete(user_to_delete)
        db.session.commit()
        logout_user()
        flash('Contul tău a fost șters', 'success')
        return redirect(url_for('index'))
    
    if current_user.role == 'admin':
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Utilizatorul {user_to_delete.username} a fost șters', 'success')
        return redirect(url_for('manage_users'))
    
    return jsonify({'error': 'Forbidden'}), 403

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)