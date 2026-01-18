# ORM-ul SQLAlchemy integrat cu Flask (mapare clase Python <-> tabele DB)
from flask_sqlalchemy import SQLAlchemy

# UserMixin oferă implementări default pentru Flask-Login:
# is_authenticated, is_active, is_anonymous, get_id()
from flask_login import UserMixin

# Funcții pentru hash-uirea parolei și verificare (NU salvezi parola în clar)
from werkzeug.security import generate_password_hash, check_password_hash

# Pentru default-uri de timp (created_at, date_added etc.)
from datetime import datetime


# Instanța SQLAlchemy; de obicei e inițializată în app factory cu db.init_app(app)
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    Modelul utilizatorului (tabela: users).
    UserMixin ajută la autentificare prin Flask-Login.
    """
    __tablename__ = 'users'

    # Cheie primară
    id = db.Column(db.Integer, primary_key=True)

    # Username unic, obligatoriu
    username = db.Column(db.String(80), unique=True, nullable=False)

    # Email unic, obligatoriu
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Hash-ul parolei (nu parola)
    password_hash = db.Column(db.String(255), nullable=False)

    # Rol simplu (control acces): client / angajat / admin
    role = db.Column(db.String(20), default='client', nullable=False)

    # Data creării contului (UTC)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Generează hash și îl salvează în password_hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifică parola introdusă comparând cu hash-ul salvat."""
        return check_password_hash(self.password_hash, password)

    # Helpers pentru roluri (utile în decorators / condiții în template)
    def is_admin(self):
        return self.role == 'admin'

    def is_employee(self):
        return self.role == 'angajat'

    def is_client(self):
        return self.role == 'client'


class Address(db.Model):
    """
    Adresa salvata pentru un user (optional).
    """
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    label = db.Column(db.String(80), nullable=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    address_line1 = db.Column(db.Text, nullable=False)
    address_line2 = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(120), nullable=False)
    county = db.Column(db.String(120), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='addresses')


class Category(db.Model):
    """
    Categorii de produse (ex: CD/Vinyl/Merch).
    """
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Product(db.Model):
    """
    Modelul produselor (tabela: products).
    Reprezintă un album/merch în catalog.
    """
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    # Titlul produsului (ex: album)
    title = db.Column(db.String(120), nullable=False)

    # Artistul
    artist = db.Column(db.String(120), nullable=False)

    # Prețul (Float e ok pentru proiect, dar în producție se preferă Decimal/Numeric)
    price = db.Column(db.Float, nullable=False)

    # URL imagine (Text ca să accepte linkuri lungi)
    image_url = db.Column(db.Text)

    # URL audio preview (opțional)
    audio_url = db.Column(db.String(500), nullable=True)

    # Descriere (opțional)
    description = db.Column(db.Text, nullable=True)

    # Stoc (implicit 0)
    stock = db.Column(db.Integer, default=0)

    # Categoria (ex: CD/Vinyl/Merch)
    category = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    category_ref = db.relationship('Category')

    # Data adăugării în catalog
    date_added = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    """
    Modelul comenzilor (tabela: orders).
    Are compatibilitate cu o schemă veche (legacy) prin câmpuri/aliasuri.
    """
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)

    # Legătură către user; nullable=False => fiecare comandă aparține unui user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # ---- Compatibilitate legacy ----
    # Dacă DB veche folosea nume total_price / date_ordered, le păstrezi ca să nu rupi migrarea.
    total_price = db.Column('total_price', db.Float, nullable=True)
    date_ordered = db.Column('date_ordered', db.DateTime, nullable=True)

    # ---- Câmpuri preferate în aplicație ----
    # Status comandă (workflow)
    status = db.Column(
        db.String(20),
        default='pending',
        nullable=False
    )  # pending/paid/processing/shipped/cancelled

    # Date livrare
    shipping_address = db.Column(db.Text)
    shipping_name = db.Column(db.String(120), nullable=True)
    shipping_phone = db.Column(db.String(50), nullable=True)

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relația 1 -> N (o comandă are mai multe item-uri)
    # cascade='all, delete-orphan' => dacă ștergi comanda, ștergi și item-urile
    items = db.relationship(
        'OrderItem',
        backref='order',
        cascade='all, delete-orphan'
    )
    status_history = db.relationship(
        'OrderStatusHistory',
        backref='order',
        cascade='all, delete-orphan'
    )

    # ---- Proprietăți pentru compatibilitate / alias ----
    @property
    def total_amount(self):
        """Alias “safe” pentru total: dacă total_price e None, întoarce 0.0."""
        return self.total_price if self.total_price is not None else 0.0

    @total_amount.setter
    def total_amount(self, value):
        """Setează totalul prin alias."""
        self.total_price = value

    @property
    def date_created(self):
        """
        Alias pentru “data comenzii”.
        Preferă created_at; dacă nu există (legacy), folosește date_ordered.
        """
        return self.created_at or self.date_ordered

    @date_created.setter
    def date_created(self, value):
        """Permite setarea prin alias (scrie în created_at)."""
        self.created_at = value


class OrderItem(db.Model):
    """
    Linie de comandă (tabela: order_items).
    Leagă o comandă de un produs + cantitate + preț la momentul cumpărării.
    """
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)

    # FK către orders
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    # FK către products
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # Cantitate cumpărată
    quantity = db.Column(db.Integer, default=1)

    # Prețul la momentul cumpărării (important: dacă se schimbă prețul produsului ulterior)
    price = db.Column(db.Float, nullable=False)

    # Relația către Product (ca să poți face item.product.title etc.)
    product = db.relationship('Product')


class OrderStatusHistory(db.Model):
    """
    Istoricul schimbarii statusului unei comenzi.
    """
    __tablename__ = 'order_status_history'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Feedback(db.Model):
    """
    Mesaje trimise din pagina de contact.
    """
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    """
    Email-uri salvate pentru newsletter.
    """
    __tablename__ = 'newsletter_subscribers'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
