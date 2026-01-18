from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Order, OrderItem, Feedback, Category, OrderStatusHistory, Address, NewsletterSubscriber
import os
from dotenv import load_dotenv
from sqlalchemy import or_, text
from sqlalchemy.exc import IntegrityError
import requests

load_dotenv()

app = Flask(__name__)

# ===== CONFIG =====
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL lipseste. Seteaza DATABASE_URL (ex: postgresql://user:pass@host:5432/dbname).")

# Unele platforme dau postgres://, dar SQLAlchemy preferă postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24 * 7

# ===== INIT EXTENSIONS =====
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@app.context_processor
def inject_pagination_url():
    def paginate_url(page):
        args = request.args.to_dict()
        args["page"] = page
        return url_for(request.endpoint, **args) + "#top"

    return {"paginate_url": paginate_url}


@app.context_processor
def inject_static_version():
    def static_version():
        try:
            css_path = os.path.join(app.root_path, "static", "styles", "main.css")
            js_path = os.path.join(app.root_path, "static", "scripts", "main.js")
            return int(max(os.path.getmtime(css_path), os.path.getmtime(js_path)))
        except Exception:
            return 1

    return {"static_version": static_version()}


@app.template_filter("six_digit")
def six_digit(value):
    try:
        return f"{int(value):06d}"
    except Exception:
        return value


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def initialize_session():
    if "cart" not in session:
        session["cart"] = []


def _seed_defaults():
    """Seed minimal: 3 useri + 1 produs demo."""
    def log_seed(message):
        print(f"[seed] {message}", flush=True)

    desired_users = [
        ("admin", "admin@music.com", "admin", "admin123"),
        ("angajat", "angajat@music.com", "angajat", "angajat123"),
        ("client", "client@gmail.com", "client", "client123"),
    ]
    for username, email, role, password in desired_users:
        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            continue
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        log_seed(f"User creat: {username} ({role})")

    for name in ("CD", "Vinyl", "Merch"):
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
            log_seed(f"Categorie creata: {name}")

    if Product.query.count() == 0:
        cd_category = Category.query.filter_by(name="CD").first()
        demo = Product(
            title="Demo Album",
            artist="Various Artists",
            price=9.99,
            stock=10,
            category="CD",
            category_id=cd_category.id if cd_category else None,
            image_url="/static/images/logo-transparent.png",
            description="Demo product for testing",
        )
        db.session.add(demo)
        log_seed("Demo product creat: Demo Album")

    db.session.commit()
    log_seed("Seed complet.")

def _initialize_database():
    lock_key = 987654
    locked = False
    try:
        if db.engine.dialect.name == "postgresql":
            db.session.execute(
                text("SELECT pg_advisory_lock(:key)"),
                {"key": lock_key},
            )
            locked = True
        db.create_all()
        _seed_defaults()
    except IntegrityError:
        db.session.rollback()
    except Exception:
        db.session.rollback()
    finally:
        if locked:
            db.session.execute(
                text("SELECT pg_advisory_unlock(:key)"),
                {"key": lock_key},
            )
            db.session.commit()


with app.app_context():
    _initialize_database()


# ===== PUBLIC ROUTES =====

@app.route("/")
def index():
    products = Product.query.order_by(Product.date_added.desc()).limit(6).all()
    return render_template("index.html", products=products)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        subject = (request.form.get("subject") or "").strip()
        message = (request.form.get("message") or "").strip()

        if not name or not email or not message:
            flash("Completeaza nume, email si mesaj.", "error")
            return redirect(url_for("contact"))

        try:
            fb = Feedback(name=name, email=email, subject=subject, message=message)
            db.session.add(fb)
            db.session.commit()
            flash("Multumim pentru mesaj! Te vom contacta in curand.", "success")
        except Exception:
            db.session.rollback()
            flash("Nu am putut salva mesajul. Incearca din nou.", "error")

        return redirect(url_for("contact"))
    return render_template("contact.html")


@app.route("/newsletter", methods=["POST"])
def newsletter_subscribe():
    email = (request.form.get("email") or "").strip().lower()
    if not email or "@" not in email:
        flash("Introdu un email valid pentru newsletter.", "error")
        return redirect(request.referrer or url_for("index"))

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        flash("Esti deja abonat la newsletter.", "info")
        return redirect(request.referrer or url_for("index"))

    try:
        db.session.add(NewsletterSubscriber(email=email))
        db.session.commit()
        flash("Te-ai abonat cu succes!", "success")
    except Exception:
        db.session.rollback()
        flash("Nu am putut salva email-ul. Incearca din nou.", "error")

    return redirect(request.referrer or url_for("index"))


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template("product_detail.html", product=product)


@app.route("/catalog")
def catalog():
    search_query = request.args.get("q")
    category = request.args.get("category")
    artist = request.args.get("artist")
    min_price = request.args.get("min_price")
    max_price = request.args.get("max_price")
    sort_by = request.args.get("sort")
    page = request.args.get("page", 1, type=int)

    query = Product.query

    # --- SEARCH (cu termeni multipli) ---
    if search_query:
        terms = search_query.split()
        for term in terms:
            term_pattern = f"%{term}%"
            query = query.filter(
                or_(
                    Product.title.ilike(term_pattern),
                    Product.artist.ilike(term_pattern),
                    Product.description.ilike(term_pattern),
                )
            )

    # --- FILTERS ---
    if category and category != "":
        query = query.filter(Product.category == category)

    if artist:
        query = query.filter(Product.artist.ilike(f"%{artist}%"))

    # FIX: acceptă și zecimale la min/max price
    if min_price:
        try:
            mp = float(min_price)
            query = query.filter(Product.price >= mp)
        except ValueError:
            pass

    if max_price:
        try:
            xp = float(max_price)
            query = query.filter(Product.price <= xp)
        except ValueError:
            pass

    # --- SORT ---
    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort_by == "name_asc":
        query = query.order_by(Product.title.asc())
    else:
        query = query.order_by(Product.id.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    products = pagination.items

    return render_template(
        "catalog.html",
        products=products,
        pagination=pagination,
        values=request.args,
    )


# ===== AUTH ROUTES =====

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not username or not email or not password:
            flash("Completează username, email și parolă.", "error")
            return redirect(url_for("register"))

        # FIX: verifică și username și email (email e unique în model)
        if User.query.filter_by(username=username).first():
            flash("Utilizatorul deja există", "error")
            return redirect(url_for("register"))
        if User.query.filter_by(email=email).first():
            flash("Email-ul este deja folosit.", "error")
            return redirect(url_for("register"))

        try:
            user = User(username=username, email=email, role="client")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Nu s-a putut crea contul (username/email deja existent).", "error")
            return redirect(url_for("register"))
        except Exception as e:
            db.session.rollback()
            flash(f"Eroare: {str(e)}", "error")
            return redirect(url_for("register"))

        flash("Contul creat cu succes! Autentifică-te acum.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        identifier_email = identifier.lower()
        user = User.query.filter(
            or_(
                User.username == identifier,
                User.email == identifier_email,
            )
        ).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Bine ai venit, {user.username}!", "success")
            # suport pentru ?next=/ruta
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))

        flash("Utilizator sau parola gresit", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Te-ai deconectat cu succes", "success")
    return redirect(url_for("index"))


# ===== DASHBOARD ROUTES =====

@app.route("/dashboard")
@login_required
def dashboard():
    stats = {}

    if current_user.role == "admin":
        stats["total_users"] = User.query.count()
        stats["total_products"] = Product.query.count()
        stats["low_stock"] = Product.query.filter(Product.stock < 5).count()

        stats["total_orders"] = Order.query.count()
        stats["pending_orders"] = Order.query.filter_by(status="pending").count()
        stats["shipped_orders"] = Order.query.filter_by(status="shipped").count()

        from sqlalchemy import func

        total_revenue = db.session.query(func.coalesce(func.sum(Order.total_price), 0)).scalar()
        stats["total_revenue"] = float(total_revenue or 0)

        # FIX MAJOR (PostgreSQL): join explicit + group_by complet
        top_products = (
            db.session.query(
                Product.title,
                Product.artist,
                func.coalesce(func.sum(OrderItem.quantity), 0).label("qty_sold"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Product.id, Product.title, Product.artist)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
            .all()
        )
        stats["top_products"] = [{"title": p[0], "artist": p[1], "qty": int(p[2] or 0)} for p in top_products]

    elif current_user.role == "angajat":
        stats["out_of_stock"] = Product.query.filter(Product.stock == 0).count()
        stats["pending_orders"] = Order.query.filter_by(status="pending").count()

        from datetime import datetime

        today = datetime.utcnow().date()
        stats["orders_today"] = (
            Order.query.filter(db.func.date(Order.created_at) == today).count()
        )

    return render_template("/dashboard/dashboard.html", user=current_user, stats=stats)


@app.route("/dashboard/orders")
@login_required
def my_orders():
    if current_user.role != "client":
        return redirect(url_for("dashboard"))
    try:
        page = request.args.get("page", 1, type=int)
        pagination = (
            Order.query.filter_by(user_id=current_user.id)
            .order_by(Order.created_at.desc())
            .paginate(page=page, per_page=12, error_out=False)
        )
        orders = pagination.items
    except Exception as e:
        app.logger.error("Failed to load orders for user %s: %s", current_user.id, e)
        flash("Încă nu este posibil să afișăm comenzile: schema bazei de date nu este actualizată.", "error")
        orders = []
        pagination = None
    return render_template("dashboard/orders.html", orders=orders, pagination=pagination)


@app.route("/dashboard/settings")
@login_required
def settings():
    addresses = []
    if current_user.role == "client":
        addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.created_at.desc()).all()
    return render_template("dashboard/settings.html", user=current_user, addresses=addresses)


@app.route("/dashboard/settings/profile", methods=["POST"])
@login_required
def update_profile():
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()

    if not username or not email:
        flash("Completeaza username si email.", "error")
        return redirect(url_for("settings"))

    if username != current_user.username and User.query.filter_by(username=username).first():
        flash("Username-ul este deja folosit.", "error")
        return redirect(url_for("settings"))
    if email != current_user.email and User.query.filter_by(email=email).first():
        flash("Email-ul este deja folosit.", "error")
        return redirect(url_for("settings"))

    try:
        current_user.username = username
        current_user.email = email
        db.session.commit()
        flash("Datele de cont au fost actualizate.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare la actualizare: {str(e)}", "error")

    return redirect(url_for("settings"))


@app.route("/dashboard/settings/password", methods=["POST"])
@login_required
def update_password():
    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""
    confirm_password = request.form.get("confirm_password") or ""

    if not current_password or not new_password or not confirm_password:
        flash("Completeaza toate campurile de parola.", "error")
        return redirect(url_for("settings"))

    if not current_user.check_password(current_password):
        flash("Parola actuala este gresita.", "error")
        return redirect(url_for("settings"))

    if new_password != confirm_password:
        flash("Parolele noi nu coincid.", "error")
        return redirect(url_for("settings"))

    if len(new_password) < 6:
        flash("Parola noua trebuie sa aiba cel putin 6 caractere.", "error")
        return redirect(url_for("settings"))

    try:
        current_user.set_password(new_password)
        db.session.commit()
        flash("Parola a fost actualizata.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare la actualizare: {str(e)}", "error")

    return redirect(url_for("settings"))


@app.route("/dashboard/addresses/add", methods=["POST"])
@login_required
def add_address():
    if current_user.role != "client":
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))

    label = (request.form.get("label") or "").strip()
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    address_line1 = (request.form.get("address_line1") or "").strip()
    address_line2 = (request.form.get("address_line2") or "").strip()
    city = (request.form.get("city") or "").strip()
    county = (request.form.get("county") or "").strip()
    postal_code = (request.form.get("postal_code") or "").strip()

    if not name or not phone or not address_line1 or not city:
        flash("Completeaza campurile obligatorii pentru adresa.", "error")
        return redirect(url_for("settings"))

    try:
        address = Address(
            user_id=current_user.id,
            label=label or None,
            name=name,
            phone=phone,
            address_line1=address_line1,
            address_line2=address_line2 or None,
            city=city,
            county=county or None,
            postal_code=postal_code or None,
        )
        db.session.add(address)
        db.session.commit()
        flash("Adresa a fost salvata.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare la salvare: {str(e)}", "error")

    return redirect(url_for("settings"))


@app.route("/dashboard/addresses/<int:address_id>/update", methods=["POST"])
@login_required
def update_address(address_id):
    if current_user.role != "client":
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))

    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        abort(403)

    label = (request.form.get("label") or "").strip()
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    address_line1 = (request.form.get("address_line1") or "").strip()
    address_line2 = (request.form.get("address_line2") or "").strip()
    city = (request.form.get("city") or "").strip()
    county = (request.form.get("county") or "").strip()
    postal_code = (request.form.get("postal_code") or "").strip()

    if not name or not phone or not address_line1 or not city:
        flash("Completeaza campurile obligatorii pentru adresa.", "error")
        return redirect(url_for("settings"))

    try:
        address.label = label or None
        address.name = name
        address.phone = phone
        address.address_line1 = address_line1
        address.address_line2 = address_line2 or None
        address.city = city
        address.county = county or None
        address.postal_code = postal_code or None
        db.session.commit()
        flash("Adresa a fost actualizata.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare la actualizare: {str(e)}", "error")

    return redirect(url_for("settings"))


@app.route("/dashboard/addresses/<int:address_id>/delete", methods=["POST"])
@login_required
def delete_address(address_id):
    if current_user.role != "client":
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))

    address = Address.query.get_or_404(address_id)
    if address.user_id != current_user.id:
        abort(403)

    try:
        db.session.delete(address)
        db.session.commit()
        flash("Adresa a fost stearsa.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare la stergere: {str(e)}", "error")

    return redirect(url_for("settings"))


@app.route("/dashboard/process-orders")
@login_required
def process_orders():
    if current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))
    try:
        page = request.args.get("page", 1, type=int)
        pagination = (
            Order.query.order_by(Order.created_at.desc())
            .paginate(page=page, per_page=12, error_out=False)
        )
        orders = pagination.items
    except Exception as e:
        app.logger.error("Failed to load orders for processing: %s", e)
        flash("Nu se pot încărca comenzile: schema bazei de date nu este actualizată.", "error")
        orders = []
        pagination = None
    return render_template("dashboard/process_orders.html", orders=orders, pagination=pagination)


@app.route("/dashboard/inventory")
@login_required
def inventory():
    if current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))

    search_query = request.args.get("q")
    category_filter = request.args.get("category")
    stock_filter = request.args.get("stock_status")

    query = Product.query

    if search_query:
        term = f"%{search_query}%"
        query = query.filter(
            or_(
                Product.title.ilike(term),
                Product.artist.ilike(term),
            )
        )

    if category_filter and category_filter != "":
        query = query.filter(Product.category == category_filter)

    if stock_filter:
        if stock_filter == "out":
            query = query.filter(Product.stock == 0)
        elif stock_filter == "low":
            query = query.filter(Product.stock < 5, Product.stock > 0)
        elif stock_filter == "ok":
            query = query.filter(Product.stock >= 5)

    query = query.order_by(Product.stock.asc(), Product.id.desc())
    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    products = pagination.items

    return render_template(
        "dashboard/inventory.html",
        products=products,
        values=request.args,
        pagination=pagination,
    )


@app.route("/dashboard/users")
@login_required
def manage_users():
    if current_user.role != "admin":
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))
    page = request.args.get("page", 1, type=int)
    pagination = User.query.order_by(User.date_created.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    users = pagination.items
    return render_template("dashboard/manage_users.html", users=users, pagination=pagination)


@app.route("/dashboard/messages")
@login_required
def dashboard_messages():
    if current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))
    page = request.args.get("page", 1, type=int)
    pagination = Feedback.query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    messages = pagination.items
    return render_template(
        "dashboard/messages.html",
        messages=messages,
        pagination=pagination,
    )


@app.route("/add_product", methods=["GET", "POST"])
@login_required
def add_product():
    if current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis! Doar angajații și adminii pot adăuga produse.", "error")
        abort(403)

    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        artist = (request.form.get("artist") or "").strip()
        price = request.form.get("price")
        stock = request.form.get("stock")
        category = (request.form.get("category") or "").strip()
        image_url = (request.form.get("image_url") or "").strip()
        audio_url = (request.form.get("audio_url") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not title or not artist or not category:
            flash("Completează title, artist și category.", "error")
            return redirect(url_for("add_product"))

        try:
            price_val = float(price)
            stock_val = int(stock)
            if price_val < 0 or stock_val < 0:
                raise ValueError("Price/stock trebuie să fie >= 0.")
        except Exception:
            flash("Preț sau stoc invalid.", "error")
            return redirect(url_for("add_product"))

        try:
            category_ref = Category.query.filter_by(name=category).first()
            product = Product(
                title=title,
                artist=artist,
                price=price_val,
                stock=stock_val,
                category=category,
                category_id=category_ref.id if category_ref else None,
                image_url=image_url,
                audio_url=audio_url or None,
                description=description,
            )
            db.session.add(product)
            db.session.commit()
            flash("Produsul a fost adăugat cu succes!", "success")
            return redirect(url_for("inventory"))
        except Exception as e:
            db.session.rollback()
            flash(f"Eroare: {str(e)}", "error")
            return redirect(url_for("add_product"))

    return render_template("/dashboard/add_product.html")


@app.route("/delete_product/<int:product_id>", methods=["POST"])
@login_required
def delete_product(product_id):
    if current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis! Nu ai permisiunea de a șterge produse.", "error")
        return redirect(url_for("inventory"))

    product = Product.query.get_or_404(product_id)

    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Produsul "{product.title}" a fost șters din catalog.', "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare la ștergere: {str(e)}", "error")

    return redirect(url_for("inventory"))


@app.route("/edit_product/<int:product_id>", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    if current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis!", "error")
        return redirect(url_for("inventory"))

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":
        try:
            product.title = (request.form.get("title") or "").strip()
            product.artist = (request.form.get("artist") or "").strip()
            product.price = float(request.form.get("price"))
            product.stock = int(request.form.get("stock"))
            product.category = (request.form.get("category") or "").strip()
            category_ref = Category.query.filter_by(name=product.category).first()
            product.category_id = category_ref.id if category_ref else None
            product.image_url = (request.form.get("image_url") or "").strip()
            product.audio_url = (request.form.get("audio_url") or "").strip() or None
            product.description = (request.form.get("description") or "").strip()

            if product.price < 0 or product.stock < 0:
                raise ValueError("Price/stock trebuie să fie >= 0.")
            if not product.title or not product.artist or not product.category:
                raise ValueError("Title/artist/category sunt obligatorii.")

            db.session.commit()
            flash("Produsul a fost actualizat!", "success")
            return redirect(url_for("inventory"))
        except Exception as e:
            db.session.rollback()
            flash(f"Eroare la actualizare: {str(e)}", "error")

    return render_template("dashboard/edit_product.html", product=product)


# ===== USER MANAGEMENT =====

@app.route("/add_user", methods=["POST"])
@login_required
def add_user():
    if current_user.role != "admin":
        flash("Acces interzis!", "error")
        return redirect(url_for("dashboard"))

    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""
    role = (request.form.get("role") or "client").strip()

    if not username or not email or not password:
        flash("Completează username, email și parolă.", "error")
        return redirect(url_for("manage_users"))

    if User.query.filter_by(username=username).first():
        flash("Utilizatorul există deja.", "error")
        return redirect(url_for("manage_users"))
    if User.query.filter_by(email=email).first():
        flash("Email-ul este deja folosit.", "error")
        return redirect(url_for("manage_users"))

    try:
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f"Utilizatorul {username} a fost creat!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Eroare: {str(e)}", "error")

    return redirect(url_for("manage_users"))


@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)

    if current_user.role == "client":
        if current_user.id != user_id:
            return jsonify({"error": "Forbidden"}), 403
        db.session.delete(user_to_delete)
        db.session.commit()
        logout_user()
        flash("Contul tău a fost șters", "success")
        return redirect(url_for("index"))

    if current_user.role == "admin":
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"Utilizatorul {user_to_delete.username} a fost șters", "success")
        return redirect(url_for("manage_users"))

    return jsonify({"error": "Forbidden"}), 403


@app.route("/checkout")
@login_required
def checkout():
    if current_user.role != "client":
        flash("Acces interzis", "error")
        return redirect(url_for("dashboard"))
    addresses = Address.query.filter_by(user_id=current_user.id).order_by(Address.created_at.desc()).all()
    return render_template("checkout.html", addresses=addresses)


@app.route("/api/checkout", methods=["POST"])
@login_required
def api_checkout():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid payload"}), 400

    cart = data.get("cart", [])
    shipping_address = (data.get("shippingaddress") or "").strip()
    shipping_name = (data.get("shippingname") or "").strip()
    shipping_phone = (data.get("shippingphone") or "").strip()

    if not cart:
        return jsonify({"error": "Cart gol"}), 400

    if not shipping_address or not shipping_name or not shipping_phone:
        return jsonify({"error": "Missing shipping information"}), 400

    try:
        from collections import defaultdict

        qty = defaultdict(int)
        ids = set()

        for item in cart:
            pid = item.get("id") or item.get("product_id")
            try:
                pid = int(pid)
            except Exception:
                return jsonify({"error": "Invalid product id in cart"}), 400

            try:
                q = int(item.get("quantity", 1))
            except Exception:
                return jsonify({"error": "Invalid quantity in cart"}), 400

            if q <= 0:
                return jsonify({"error": "Quantity must be >= 1", "product_id": pid}), 400

            qty[pid] += q
            ids.add(pid)

        products = Product.query.filter(Product.id.in_(ids)).all()
        if len(products) != len(ids):
            return jsonify({"error": "Unele produse nu au fost gasite"}), 404

        total = 0.0
        for p in products:
            q = qty[p.id]
            if p.stock < q:
                return jsonify({"error": f"Stoc insuficient pentru {p.title}", "product_id": p.id}), 400
            total += p.price * q

        order = Order(
            user_id=current_user.id,
            total_amount=total,  # property -> scrie în total_price
            shipping_address=shipping_address,
            shipping_name=shipping_name,
            shipping_phone=shipping_phone,
        )
        db.session.add(order)
        db.session.flush()
        db.session.add(
            OrderStatusHistory(
                order_id=order.id,
                status=order.status or "pending",
                note="Order created",
            )
        )

        for p in products:
            q = qty[p.id]
            oi = OrderItem(order_id=order.id, product_id=p.id, quantity=q, price=p.price)
            db.session.add(oi)
            p.stock -= q

        db.session.commit()
        return jsonify({"success": True, "order_id": order.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/order-confirmation/<int:order_id>")
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and current_user.role not in ["angajat", "admin"]:
        flash("Acces interzis", "error")
        return redirect(url_for("index"))
    return render_template("order_confirmation.html", order=order)


@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    if current_user.role not in ["angajat", "admin"]:
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Missing status"}), 400

    order = Order.query.get_or_404(order_id)
    order.status = new_status
    db.session.add(
        OrderStatusHistory(
            order_id=order.id,
            status=new_status,
            note=f"Status updated by {current_user.username}",
        )
    )
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    if order.status != "pending":
        return jsonify({"error": "Doar comenzile în status pending pot fi anulate"}), 400

    try:
        for item in order.items:
            item.product.stock += item.quantity

        order.status = "cancelled"
        db.session.add(
            OrderStatusHistory(
                order_id=order.id,
                status="cancelled",
                note=f"Cancelled by {current_user.username}",
            )
        )
        db.session.commit()
        return jsonify({"success": True, "message": "Comanda a fost anulată cu succes"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/api/orders/<int:order_id>", methods=["DELETE"])
@login_required
def delete_order(order_id):
    if current_user.role not in ["angajat", "admin"]:
        return jsonify({"error": "Forbidden"}), 403

    order = Order.query.get_or_404(order_id)

    try:
        for item in order.items:
            item.product.stock += item.quantity

        db.session.delete(order)
        db.session.commit()
        return jsonify({"success": True, "message": "Comanda a fost ștearsă cu succes"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ===== API ENDPOINTS PENTRU RAPOARTE =====

@app.route("/api/dashboard/stats", methods=["GET"])
@login_required
def get_dashboard_stats():
    if current_user.role == "admin":
        from sqlalchemy import func
        from datetime import datetime

        stats = {}

        stats["total_orders"] = Order.query.count()
        stats["pending_orders"] = Order.query.filter_by(status="pending").count()
        stats["shipped_orders"] = Order.query.filter_by(status="shipped").count()
        stats["cancelled_orders"] = Order.query.filter_by(status="cancelled").count()

        total_revenue = db.session.query(func.coalesce(func.sum(Order.total_price), 0)).scalar()
        stats["total_revenue"] = float(total_revenue or 0)

        today = datetime.utcnow().date()
        today_revenue = (
            db.session.query(func.coalesce(func.sum(Order.total_price), 0))
            .filter(db.func.date(Order.created_at) == today)
            .scalar()
        )
        stats["today_revenue"] = float(today_revenue or 0)

        stats["total_users"] = User.query.filter_by(role="client").count()

        stats["total_products"] = Product.query.count()
        stats["low_stock"] = Product.query.filter(Product.stock < 5).count()

        return jsonify(stats)

    return jsonify({"error": "Forbidden"}), 403


@app.route("/api/dashboard/top-products", methods=["GET"])
@login_required
def get_top_products():
    if current_user.role not in ["admin", "angajat"]:
        return jsonify({"error": "Forbidden"}), 403

    from sqlalchemy import func

    # FIX MAJOR (PostgreSQL): join explicit + group_by complet
    top_products = (
        db.session.query(
            Product.id,
            Product.title,
            Product.artist,
            Product.price,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("qty_sold"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.price), 0).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .group_by(Product.id, Product.title, Product.artist, Product.price)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    result = [
        {
            "id": p[0],
            "title": p[1],
            "artist": p[2],
            "price": float(p[3]),
            "qty_sold": int(p[4] or 0),
            "revenue": float(p[5] or 0),
        }
        for p in top_products
    ]

    return jsonify(result)


@app.route("/api/dashboard/orders-by-date", methods=["GET"])
@login_required
def get_orders_by_date():
    if current_user.role not in ["admin", "angajat"]:
        return jsonify({"error": "Forbidden"}), 403

    from sqlalchemy import func
    from datetime import datetime, timedelta

    days_back = request.args.get("days", 30, type=int)
    start_date = datetime.utcnow().date() - timedelta(days=days_back)

    orders_by_date = (
        db.session.query(
            db.func.date(Order.created_at).label("date"),
            func.count(Order.id).label("count"),
            func.coalesce(func.sum(Order.total_price), 0).label("revenue"),
        )
        .filter(Order.created_at >= start_date)
        .group_by(db.func.date(Order.created_at))
        .order_by(db.func.date(Order.created_at))
        .all()
    )

    result = [
        {"date": str(row[0]), "count": int(row[1]), "revenue": float(row[2] or 0)}
        for row in orders_by_date
    ]

    return jsonify(result)


# ===== QOBUZ HELPERS (SEARCH) =====

@app.route("/api/qobuz/search")
@login_required
def qobuz_search():
    if current_user.role not in ["angajat", "admin"]:
        return jsonify({"error": "Forbidden"}), 403

    term = (request.args.get("term") or "").strip()
    if not term:
        return jsonify({"error": "Missing term"}), 400
    page = request.args.get("page", 1, type=int)
    page = max(1, page)
    per_page = 10
    offset = (page - 1) * per_page

    try:
        resp = requests.get(
            "https://fabianchelu.vercel.app/api/get-music",
            params={"q": term, "offset": offset},
            timeout=10,
        )
        data = resp.json()
    except Exception:
        return jsonify({"error": "Qobuz request failed"}), 502

    if not data.get("success"):
        return jsonify({"error": "Qobuz request failed"}), 502

    payload = data.get("data") or {}
    albums = payload.get("albums") or {}
    tracks = payload.get("tracks") or {}
    preview_track_by_album = {}
    for track in tracks.get("items") or []:
        album_id = (track.get("album") or {}).get("id")
        track_id = track.get("id")
        if album_id and track_id and album_id not in preview_track_by_album:
            preview_track_by_album[album_id] = track_id
    results = []
    for album in albums.get("items") or []:
        image = album.get("image") or {}
        results.append(
            {
                "collectionId": album.get("id"),
                "collectionName": album.get("title"),
                "artistName": (album.get("artist") or {}).get("name"),
                "artworkUrl100": image.get("small") or image.get("thumbnail"),
                "artworkUrl600": image.get("large"),
                "releaseDate": album.get("release_date_original")
                or album.get("release_date_download")
                or album.get("release_date_stream"),
                "primaryGenreName": (album.get("genre") or {}).get("name"),
                "collectionType": "album",
                "previewTrackId": preview_track_by_album.get(album.get("id")),
            }
        )

    total = int(albums.get("total") or len(results))
    limit = int(albums.get("limit") or per_page)
    total_pages = max(1, (total + limit - 1) // limit)
    page = max(1, min(page, total_pages))

    return jsonify(
        {
            "items": results,
            "page": page,
            "per_page": limit,
            "total": total,
            "total_pages": total_pages,
        }
    )


@app.route("/api/qobuz/preview/<int:track_id>")
def qobuz_preview(track_id):
    quality = request.args.get("quality", 27, type=int)
    try:
        resp = requests.get(
            "https://fabianchelu.vercel.app/api/download-music",
            params={"track_id": track_id, "quality": quality},
            timeout=10,
        )
        data = resp.json()
    except Exception:
        return jsonify({"error": "Qobuz preview failed"}), 502

    if not data.get("success"):
        return jsonify({"error": "Qobuz preview failed"}), 502

    url = (data.get("data") or {}).get("url")
    if not url:
        return jsonify({"error": "Qobuz preview missing url"}), 502

    return jsonify({"url": url})


@app.route("/api/qobuz/album/<album_id>")
def qobuz_album(album_id):

    try:
        resp = requests.get(
            "https://fabianchelu.vercel.app/api/get-album",
            params={"album_id": album_id},
            timeout=10,
        )
        data = resp.json()
    except Exception:
        return jsonify({"error": "Qobuz album request failed"}), 502

    if not data.get("success"):
        return jsonify({"error": "Qobuz album request failed"}), 502

    album = data.get("data") or {}
    tracks = ((album.get("tracks") or {}).get("items") or [])
    track_list = []
    for t in tracks:
        track_list.append(
            {
                "id": t.get("id"),
                "title": t.get("title"),
                "duration": t.get("duration"),
                "trackNumber": t.get("track_number"),
            }
        )

    return jsonify(
        {
            "albumId": album.get("id"),
            "title": album.get("title"),
            "artistName": (album.get("artist") or {}).get("name"),
            "releaseDate": album.get("release_date_original")
            or album.get("release_date_download")
            or album.get("release_date_stream"),
            "primaryGenreName": (album.get("genre") or {}).get("name"),
            "tracks": track_list,
        }
    )


# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=604800"
    return response


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)



