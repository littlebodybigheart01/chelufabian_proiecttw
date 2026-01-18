import argparse
import html
import os
import random
import re
import time
from datetime import datetime

import requests

from app import app, db
from models import Category, Product, Order, OrderItem


API_BASE = "https://fabianchelu.vercel.app/api"
DEFAULT_TIMEOUT = 20

ARTISTS = [
    "Britney Spears",
    "Lady Gaga",
    "Melanie Martinez",
    "Jazmin Bean",
    "Doja Cat",
    "Rihanna",
    "Cardi B",
    "Miley Cyrus",
    "Sabrina Carpenter",
    "Kesha",
    "Kylie Minogue",
    "Fergie",
    "Christina Aguilera",
    "Ariana Grande",
    "Billie Eilish",
    "Selena Gomez",
    "Demi Lovato",
    "Halsey",
    "Camila Cabello",
    "Zara Larsson",
    "Frank Ocean",
    "The Weeknd",
    "Lana Del Rey",
    "Kendrick Lamar",
    "Charli XCX",
    "Rosalia",
    "Addison Rae",
    "Olivia Rodrigo",
    "Chappell Roan",
    "SZA",
    "Tate McRae",
    "Lorde",
    "Tyler, The Creator",
    "A$AP Rocky",
    "Drake",
    "Travis Scott",
    "Beyonce",
    "Madonna",
    "Megan Thee Stallion",
    "CupcakKe",
    "Playboi Carti",
    "Mariah Carey",
    "Irina Rimes",
]


def clean_html(text):
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return html.unescape(cleaned).strip()


def format_release_date(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value).strftime("%Y-%m-%d")
        except Exception:
            return ""
    if isinstance(value, str):
        return value[:10]
    return ""


def fetch_json(endpoint, params):
    resp = requests.get(
        f"{API_BASE}/{endpoint}",
        params=params,
        timeout=DEFAULT_TIMEOUT,
    )
    data = resp.json()
    if not data.get("success"):
        return None
    return data.get("data") or {}


def iter_artist_albums(artist, max_albums=None, sleep_s=0.25):
    offset = 0
    seen = set()
    while True:
        payload = fetch_json("get-music", {"q": artist, "offset": offset})
        if not payload:
            break
        albums = payload.get("albums") or {}
        items = albums.get("items") or []
        limit = int(albums.get("limit") or len(items) or 10)
        total = int(albums.get("total") or 0)
        if not items:
            break
        for album in items:
            album_id = album.get("id")
            if not album_id or album_id in seen:
                continue
            seen.add(album_id)
            yield album
            if max_albums and len(seen) >= max_albums:
                return
        offset += limit
        if offset >= total:
            break
        time.sleep(sleep_s)


def pick_preview_track(tracks):
    if not tracks:
        return None

    def score(track):
        for key in ("popularity", "rank", "listen_count", "stream_count"):
            value = track.get(key)
            if isinstance(value, (int, float)):
                return value
        return None

    scored = [(score(track), track) for track in tracks]
    if any(val is not None for val, _ in scored):
        best = max(scored, key=lambda item: (item[0] is not None, item[0] or 0))[1]
        return best.get("id")

    ordered = sorted(
        tracks,
        key=lambda track: (
            track.get("track_number") is None,
            track.get("track_number") or 0,
        ),
    )
    return ordered[0].get("id")


def ensure_categories():
    for name in ("CD", "Vinyl"):
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()


def pick_category():
    return random.choice(["CD", "Vinyl"])


def pick_price(category):
    if category == "CD":
        cents = random.randint(3999, 9999)
    else:
        cents = random.randint(9999, 39999)
    return cents / 100.0


def generate_product_id(used_ids):
    while True:
        candidate = random.randint(100000, 999999)
        if candidate not in used_ids:
            used_ids.add(candidate)
            return candidate


def build_description(album):
    description = clean_html(album.get("description") or "")
    if description:
        return description
    parts = []
    title = album.get("title") or "Album"
    artist = (album.get("artist") or {}).get("name") or ""
    genre = (album.get("genre") or {}).get("name") or ""
    release_date = format_release_date(
        album.get("release_date_original")
        or album.get("release_date_download")
        or album.get("release_date_stream")
    )
    parts.append(f"Album: {title}")
    if artist:
        parts.append(f"Artist: {artist}")
    if genre:
        parts.append(f"Gen: {genre}")
    if release_date:
        parts.append(f"Lansat: {release_date}")
    return "\n".join(parts)


def refresh_products(max_albums_per_artist, wipe_orders):
    def log(message):
        print(f"[refresh] {message}", flush=True)

    ensure_categories()

    if wipe_orders:
        log("Sterg order_items si orders...")
        db.session.query(OrderItem).delete()
        db.session.query(Order).delete()
        db.session.commit()

    log("Sterg produsele existente...")
    db.session.query(Product).delete()
    db.session.commit()

    cd_category = Category.query.filter_by(name="CD").first()
    vinyl_category = Category.query.filter_by(name="Vinyl").first()

    created = 0
    seen_album_ids = set()
    used_ids = set()
    for artist in ARTISTS:
        log(f"Artist: {artist}")
        artist_created = 0
        for album in iter_artist_albums(artist, max_albums=max_albums_per_artist):
            album_id = album.get("id")
            if not album_id or album_id in seen_album_ids:
                continue
            seen_album_ids.add(album_id)

            album_details = fetch_json("get-album", {"album_id": album_id}) or {}
            tracks = ((album_details.get("tracks") or {}).get("items") or [])
            preview_track_id = pick_preview_track(tracks)

            category = pick_category()
            price = pick_price(category)
            stock = random.randint(6, 40)
            image = album.get("image") or {}
            image_url = image.get("large") or image.get("small") or image.get("thumbnail")
            description = build_description(album_details or album)
            product_id = generate_product_id(used_ids)

            product = Product(
                id=product_id,
                title=album.get("title") or album_details.get("title") or "Album",
                artist=(album.get("artist") or {}).get("name")
                or (album_details.get("artist") or {}).get("name")
                or artist,
                price=price,
                stock=stock,
                category=category,
                category_id=cd_category.id if category == "CD" else vinyl_category.id,
                image_url=image_url,
                description=description,
                audio_url=f"qobuz:{preview_track_id}|{album_id}"
                if preview_track_id
                else None,
            )
            db.session.add(product)
            created += 1
            artist_created += 1
            if created % 10 == 0:
                log(f"Produse create: {created}")
        db.session.commit()
        if artist_created:
            log(f"Total pentru {artist}: {artist_created}")

    if db.engine.dialect.name == "postgresql":
        try:
            db.session.execute(
                "SELECT setval(pg_get_serial_sequence('products','id'), "
                "(SELECT MAX(id) FROM products));"
            )
            db.session.commit()
            log("Secventa products.id actualizata.")
        except Exception:
            db.session.rollback()

    log(f"Import complet. Total produse: {created}")
    return created


def parse_args():
    parser = argparse.ArgumentParser(
        description="Refresh products from Qobuz API with CD/Vinyl only."
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirma ca vrei sa stergi produsele existente.",
    )
    parser.add_argument(
        "--max-albums",
        type=int,
        default=0,
        help="Limita optionala de albume per artist (0 = toate).",
    )
    parser.add_argument(
        "--wipe-orders",
        action="store_true",
        help="Sterge si comenzile + item-urile (daca exista).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.confirm:
        raise SystemExit(
            "Ruleaza din nou cu --confirm ca sa stergi produsele existente."
        )
    max_albums = args.max_albums if args.max_albums and args.max_albums > 0 else None
    with app.app_context():
        created = refresh_products(max_albums, args.wipe_orders)
    print(f"Import complet. Produse create: {created}")


if __name__ == "__main__":
    main()
