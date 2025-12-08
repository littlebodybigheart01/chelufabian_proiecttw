# Garden of Records - Music Store

Magazin online de muzică construit cu Flask și bază de date PostgreSQL.

## Caracteristici

- **Design Elegant**: Header cu gradient gri animat și particule glitter
- **Responsive**: Design mobil-first adaptat pentru toate dispozitivele
- **Gestionare Produse**: Categorii de CD-uri, Vinyl-uri și Merchandise
- **Sistem de Rol**: Client, Angajat și Admin cu permisiuni diferite
- **Coș de Cumpărături**: Gestionat cu localStorage pentru frontend
- **Autentificare**: Sistem de login și register cu hashing de parolă
- **Dashboard Personalizat**: Fiecare rol are acces la funcționalități specifice

## Cerințe de Securitate Implementate

### Reguli Critice de Șters Cont:
1. **Client**: Poate șterge DOAR propriul cont din Settings
2. **Angajat**: NU poate șterge niciun cont (403 Forbidden)
3. **Admin**: Poate șterge orice cont din User Management

## Setup și Lansare

### Opțiunea 1: Cu Docker (Recomandat)

\`\`\`bash
# Clonează proiectul
git clone <repository-url>
cd garden-of-records

# Creează .env din template
cp .env.example .env

# Lansează containerele
docker-compose up -d

# Seed-ează baza de date
docker-compose exec web python seed.py

# Accesează aplicația
open http://localhost:5000
\`\`\`

### Opțiunea 2: Local Development

\`\`\`bash
# Instalează Python 3.11+
python --version

# Creează virtual environment
python -m venv venv
source venv/bin/activate  # Pe Windows: venv\Scripts\activate

# Instalează dependențe
pip install -r requirements.txt

# Creează .env
cp .env.example .env

# Pentru SQLite local, actualizează DATABASE_URL în .env:
# DATABASE_URL=sqlite:///garden_records.db

# Runn seed script
python seed.py

# Lansează Flask
python app.py

# Accesează pe http://localhost:5000
\`\`\`

## Credențiale Default

După rularea seed script-ului:
- **Username**: admin
- **Email**: admin@music.com
- **Password**: password

⚠️ IMPORTANT: Schimbă parola admin în producție!

## Structura Proiectului

\`\`\`
garden-of-records/
├── app.py                 # Main Flask application
├── models.py              # Database models (User, Product)
├── seed.py                # Database seeding script
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker Compose setup
├── .env.example           # Environment variables template
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template cu design
│   ├── index.html        # Homepage
│   ├── cd.html           # CD-uri page
│   ├── vinyl.html        # Vinyl-uri page
│   ├── merch.html        # Merchandise page
│   ├── contact.html      # Contact page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── product_detail.html  # Product detail page
│   ├── dashboard.html    # Dashboard hub
│   └── dashboard/        # Role-specific dashboards
│       ├── settings.html      # Client settings + delete account
│       ├── manage_users.html  # Admin user management
│       ├── orders.html        # Client orders
│       ├── process_orders.html # Employee orders
│       └── inventory.html     # Inventory management
└── static/
    ├── styles/
    │   ├── main.css      # Main styles cu gradient și glitter
    │   └── dashboard.css # Dashboard styles
    ├── scripts/
    │   ├── main.js       # Main functionality
    │   └── cart.js       # Shopping cart logic
    └── images/           # Product images
        ├── logo-transparent.png
        ├── britney.png
        ├── ladygaga.webp
        ├── melanie.webp
        └── glory.jpeg
\`\`\`

## Fluxul de Securitate

### Ștergerea Contului:
1. **Client** accesează Settings → Click "Șterge Contul Meu"
2. Backend verifică dacă `current_user.id == user_id_to_delete`
3. Dacă YES: Cont șters, user deconectat, redirect la home
4. Dacă NO: 403 Forbidden

### User Management (Admin Only):
1. Admin accesează Dashboard → User Management
2. Vezi tabel cu toți utilizatorii
3. Doar Admin poate apăsa butonul "Șterge"
4. Sistem: Backend refuză oricine nu e admin

## API Endpoints

### Public
- `GET /` - Homepage
- `GET /cd` - CD-uri
- `GET /vinyl` - Vinyl-uri
- `GET /merch` - Merchandise
- `GET /contact` - Contact
- `GET /product/<id>` - Product detail
- `POST /contact` - Contact form

### Authentication
- `GET /register` - Register page
- `POST /register` - Create account
- `GET /login` - Login page
- `POST /login` - Login
- `GET /logout` - Logout

### Protected (Login Required)
- `GET /dashboard` - Dashboard hub
- `GET /dashboard/orders` - My orders (Client)
- `GET /dashboard/settings` - Settings (Client)
- `POST /delete_user/<id>` - Delete account (Client own only)
- `GET /dashboard/users` - User management (Admin only)
- `POST /delete_user/<id>` - Delete user (Admin only)

## Configurare Bază de Date

### Tabelele Principale

**Users**:
- id (PK)
- username (Unique)
- email (Unique)
- password_hash
- role (client, angajat, admin)
- date_created

**Products**:
- id (PK)
- title
- artist
- price
- image_url
- stock
- category (CD, Vinyl, Merch)
- date_added

## Tehnologii Utilizate

- **Backend**: Flask 3.0.0
- **Database**: PostgreSQL 15 / SQLite
- **Authentication**: Flask-Login
- **ORM**: SQLAlchemy
- **Security**: Werkzeug password hashing
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Containerization**: Docker & Docker Compose

## Deployment

### Pentru Vercel/PaaS:
1. Setează variabile de mediu (DATABASE_URL, SECRET_KEY)
2. Rulează migrații
3. Deploys cu `gunicorn app:app`

### Pentru Producție:
- Schimbă `FLASK_ENV` la 'production'
- Setează `SECRET_KEY` la o valoare sigură
- Folosește PostgreSQL (nu SQLite)
- Setează HTTPS
- Configurează reverse proxy (Nginx)

## Suport și Contacte

- **Email**: contact@gardenofrecords.ro
- **Telefon**: +40 123 456 789
- **Adresă**: Strada Muzicii 123, București

---

Made with ❤️ for music lovers 🎵
\`\`\`

```text file="Makefile"
.PHONY: help setup run seed clean

help:
	@echo "Garden of Records - Available Commands"
	@echo "======================================"
	@echo "make setup        - Setup development environment"
	@echo "make run          - Run Flask development server"
	@echo "make seed         - Seed database with demo data"
	@echo "make docker-up    - Start Docker containers"
	@echo "make docker-down  - Stop Docker containers"
	@echo "make clean        - Clean up temporary files"

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env

run:
	python app.py

seed:
	python seed.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf venv/
	rm -f garden_records.db
