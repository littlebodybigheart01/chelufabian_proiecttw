# Garden of Records

## Romana

Aplicatie Flask completa pentru magazin de muzica (CD, Vinyl, Merch), cu integrare Qobuz pentru albume, preview audio si dashboard de administrare.

### Rezumat rapid

- Home afiseaza ultimele produse din baza de date
- Catalog cu filtre, sortare si cautare
- Product detail cu tracklist si preview per piesa
- Dashboard pentru management produse si utilizatori
- Newsletter cu salvare email

### Functionalitati detaliate

- Catalog produse cu filtre (categorie, artist, pret), sortare si cautare
- Pagina produs cu:
  - coperta + buton play/pause
  - rotatie coperta la redare
  - lista piese cu play pe fiecare track
  - evidentiere track in redare
- Cos de cumparaturi in localStorage cu modal si total calculat
- Dashboard:
  - inventar + editare/stergere
  - adaugare produs (CD/Vinyl/Merch)
  - management utilizatori si comenzi
- Integrare Qobuz prin proxy server-side (preview audio si tracklist)
- Newsletter cu email unic

### Stack

- Python 3.11
- Flask, Flask-Login, Flask-SQLAlchemy
- PostgreSQL 15
- Gunicorn
- Docker + docker compose

### Structura proiect (tree complet, fara __pycache__)

```
.
|   app.py
|   docker-compose.yml
|   Dockerfile
|   models.py
|   pnpm-lock.yaml
|   README.md
|   requirements.txt
|   
+---backups
|       garden_records_20260118-232546.sql
|       
+---images
|       logo-transparent.png
|       logo-white.png
|       
+---scripts
|       backup_db.ps1
|       backup_db.py
|       refresh_products.py
|       restore_db.ps1
|       restore_db.py
|       
+---static
|   +---images
|   |       cd.png
|   |       logo-transparent.png
|   |       merch.png
|   |       vinyl.png
|   |       
|   +---scripts
|   |       main.js
|   |       
|   \---styles
|           main.css
|           
+---templates
|   |   403.html
|   |   404.html
|   |   500.html
|   |   base.html
|   |   catalog.html
|   |   checkout.html
|   |   contact.html
|   |   index.html
|   |   login.html
|   |   order_confirmation.html
|   |   product_detail.html
|   |   register.html
|   |   
|   \---dashboard
|           add_product.html
|           dashboard.html
|           edit_product.html
|           inventory.html
|           manage_users.html
|           messages.html
|           orders.html
|           process_orders.html
|           settings.html
|           _menu.html
|           _pagination.html
```

### Variabile de mediu

Necesare:

- `DATABASE_URL` - string de conexiune Postgres

Optionale:

- `SECRET_KEY` - cheie sesiune Flask (default dev)
- `SESSION_COOKIE_SECURE` - `1`/`true` pentru cookie Secure

Exemplu:

```
DATABASE_URL=postgresql://postgres:postgres_secure_password@db:5432/garden_records
SECRET_KEY=change-me
SESSION_COOKIE_SECURE=false
```

### Rulare cu Docker

Build si start:

```
docker compose build
docker compose up -d
```

Aplicatia ruleaza la:

```
http://localhost:5000
```

Oprire:

```
docker compose down
```

Reset complet baza (sterge volumele):

```
docker compose down -v
```

### Rulare local (fara Docker)

1. Creeaza un venv
2. Instaleaza dependintele:

```
pip install -r requirements.txt
```

3. Seteaza `DATABASE_URL`
4. Ruleaza:

```
python app.py
```

### Seed si bootstrap

- La pornire se ruleaza `db.create_all()` si seed minimal
- Se creeaza useri default, categorii si un produs demo
- Seed-ul este idempotent si logheaza progresul cu `[seed] ...`
- Pentru Postgres se foloseste un advisory lock pentru a evita init simultan in multi-worker

### Useri default

- admin / admin123
- angajat / angajat123
- client / client123

### Roluri si permisiuni

- admin: acces complet la dashboard si utilizatori
- angajat: acces dashboard (inventar/comenzi)
- client: acces public (catalog, checkout, profil)

### Rute principale (publice)

- Home: landing, produse noi
- Catalog: filtre, sortare, cautare
- Product detail: preview si tracklist
- Contact: formular feedback
- Newsletter: abonare email

Rute:

- `GET /` - home, ultimele produse
- `GET /catalog` - catalog cu filtre
- `GET /product/<id>` - pagina produs
- `GET /contact` + `POST /contact` - formular contact
- `POST /newsletter` - salvare email newsletter

### Rute dashboard (auth)

Acces limitat la rolurile admin/angajat. Include CRUD produse, management utilizatori si comenzi.

- `GET /dashboard`
- `GET /inventory`
- `GET /add_product` + `POST /add_product`
- `GET /edit_product/<id>` + `POST /edit_product/<id>`
- `GET /manage_users`
- `GET /orders`

### API Qobuz (proxy)

- `GET /api/qobuz/search`
  - doar admin/angajat
  - params: `term`, `page`

- `GET /api/qobuz/album/<album_id>`
  - public

- `GET /api/qobuz/preview/<track_id>`
  - public

Audio se salveaza in format:

```
qobuz:<track_id>|<album_id>
```

### Flux Qobuz (Add Product)

1. Cauti album in dashboard
2. Selectezi rezultatul (autofill titlu/artist/cover)
3. Se incarca tracklist
4. Alegi track de preview (seteaza `audio_url`)

### Add Product (Dashboard)

- CD / Vinyl:
  - Qobuz search activ
  - tracklist + preview
  - audio_url disponibil

- Merch:
  - fara Qobuz
  - doar URL imagine
  - audio ascuns

### Cos de cumparaturi

- Stocat in `localStorage`
- Modal cu total calculat
- Butoane pentru crestere/scadere cantitate

### Newsletter

- Validare simpla email
- Evita duplicate (email unic)
- Mesaje flash pentru succes/eroare

Tabel:

```
newsletter_subscribers
```

### Model DB (tabele)

- `users`: username, email, role
- `products`: title, artist, price, image_url, audio_url, category
- `categories`: CD/Vinyl/Merch
- `orders`: status, total_price, created_at
- `order_items`: product_id, quantity, price
- `order_status_history`: status history
- `feedback`: contact messages
- `newsletter_subscribers`: emails
- `addresses`: existent, nefolosit in UI

### Scripturi

#### Refresh produse (Qobuz)

```
python scripts/refresh_products.py --confirm
```

Optiuni:

- `--max-albums N`
- `--wipe-orders`

Preturi random:

- CD: 39.99 - 99.99
- Vinyl: 99.99 - 399.99

#### Backup / Restore (SQL)

Backup:

```
python scripts/backup_db.py
```

Restore:

```
python scripts/restore_db.py backups/garden_records_YYYYMMDD-HHMMSS.sql
```

Optiuni:

- `--db` (default `garden_records`)
- `--user` (default `postgres`)
- `--host` (default `db`)
- `--port` (default `5432`)
- `--output` (doar backup)

### Note

- Pastreaza fisierele in UTF-8.
- Cache-busting pentru static este facut cu `?v=` pe CSS/JS.

---

## English

Full-stack Flask store for music albums and merchandise with Qobuz-powered album data, preview playback, cart, and admin dashboard.

### Quick summary

- Home shows latest products
- Catalog with filters, sorting, search
- Product detail with tracklist and per-track preview
- Dashboard for products and users
- Newsletter email storage

### Detailed features

- Catalog with filters (category, artist, price) and sorting
- Product detail:
  - cover play/pause button
  - cover rotation while playing
  - per-track play buttons
  - active track highlight
- Cart stored in localStorage with modal and totals
- Dashboard:
  - inventory + edit/delete
  - add product (CD/Vinyl/Merch)
  - user and order management
- Qobuz integration via server-side proxy
- Newsletter with unique email constraint

### Stack

- Python 3.11
- Flask, Flask-Login, Flask-SQLAlchemy
- PostgreSQL 15
- Gunicorn
- Docker + docker compose

### Project Structure (full tree, no __pycache__)

```
.
|   app.py
|   docker-compose.yml
|   Dockerfile
|   models.py
|   pnpm-lock.yaml
|   README.md
|   requirements.txt
|   
+---backups
|       garden_records_20260118-232546.sql
|       
+---images
|       logo-transparent.png
|       logo-white.png
|       
+---scripts
|       backup_db.ps1
|       backup_db.py
|       refresh_products.py
|       restore_db.ps1
|       restore_db.py
|       
+---static
|   +---images
|   |       cd.png
|   |       logo-transparent.png
|   |       merch.png
|   |       vinyl.png
|   |       
|   +---scripts
|   |       main.js
|   |       
|   \---styles
|           main.css
|           
+---templates
|   |   403.html
|   |   404.html
|   |   500.html
|   |   base.html
|   |   catalog.html
|   |   checkout.html
|   |   contact.html
|   |   index.html
|   |   login.html
|   |   order_confirmation.html
|   |   product_detail.html
|   |   register.html
|   |   
|   \---dashboard
|           add_product.html
|           dashboard.html
|           edit_product.html
|           inventory.html
|           manage_users.html
|           messages.html
|           orders.html
|           process_orders.html
|           settings.html
|           _menu.html
|           _pagination.html
```

### Environment Variables

Required:

- `DATABASE_URL` - PostgreSQL connection string

Optional:

- `SECRET_KEY` - Flask session secret
- `SESSION_COOKIE_SECURE` - `1`/`true` for Secure cookies

### Run with Docker

```
docker compose build
docker compose up -d
```

App:

```
http://localhost:5000
```

Stop:

```
docker compose down
```

Reset database (remove volume):

```
docker compose down -v
```

### Local Run

```
pip install -r requirements.txt
python app.py
```

### Seed and bootstrap

- App runs `db.create_all()` on startup
- Seeds default users, categories, and a demo product
- Seed is idempotent and logs `[seed] ...`
- Postgres advisory lock prevents multi-worker init races

### Default Users

- admin / admin123
- angajat / angajat123
- client / client123

### Roles and permissions

- admin: full dashboard access
- angajat: dashboard inventory/orders
- client: public site access

### Main routes

- Home: latest products
- Catalog: filters, sorting, search
- Product detail: preview and tracklist
- Contact: feedback form
- Newsletter: email subscribe

Routes:

- `GET /`
- `GET /catalog`
- `GET /product/<id>`
- `GET /contact` + `POST /contact`
- `POST /newsletter`

### Dashboard routes (auth)

Requires `admin` or `angajat`:

- `/dashboard`
- `/inventory`
- `/add_product`
- `/edit_product/<id>`
- `/manage_users`
- `/orders`

### Qobuz Proxy API

- `GET /api/qobuz/search` (admin/angajat)
- `GET /api/qobuz/album/<album_id>` (public)
- `GET /api/qobuz/preview/<track_id>` (public)

Audio format stored in DB:

```
qobuz:<track_id>|<album_id>
```

### Qobuz add product flow

1. Search album
2. Select result (autofill title/artist/cover)
3. Tracklist loads
4. Choose preview track (sets `audio_url`)

### Add Product (Dashboard)

- CD / Vinyl:
  - Qobuz search enabled
  - tracklist + preview
  - audio_url available

- Merch:
  - no Qobuz search
  - image URL only
  - audio hidden

### Cart behavior

- Stored in `localStorage`
- Modal with totals
- Quantity update buttons

### Newsletter

- Simple email validation
- Unique email constraint
- Flash messages for success/error

Table:

```
newsletter_subscribers
```

### Database tables

- `users`: username, email, role
- `products`: title, artist, price, image_url, audio_url, category
- `categories`: CD/Vinyl/Merch
- `orders`: status, total_price, created_at
- `order_items`: product_id, quantity, price
- `order_status_history`: status history
- `feedback`: contact messages
- `newsletter_subscribers`: emails
- `addresses`: exists, unused in UI

### Scripts

#### Refresh products

```
python scripts/refresh_products.py --confirm
```

Options:

- `--max-albums N`
- `--wipe-orders`

Pricing:

- CD: 39.99 - 99.99
- Vinyl: 99.99 - 399.99

#### Backup / Restore (SQL)

Backup:

```
python scripts/backup_db.py
```

Restore:

```
python scripts/restore_db.py backups/garden_records_YYYYMMDD-HHMMSS.sql
```

Options:

- `--db`
- `--user`
- `--host`
- `--port`
- `--output`

### Notes

- Keep files in UTF-8.
- Cache busting for static assets uses `?v=` on CSS/JS.
