import requests
import random
import time
from app import app, db, Product
from sqlalchemy import text

# ID-urile oficiale Apple Music pentru artisti
# Astfel mergem la sigur, fara cautari vagi
ARTIST_IDS = {
    "Britney Spears": "217005",  # Found: Britney Spears
    "Lady Gaga": "277293880",  # Found: Lady Gaga
    "Melanie Martinez": "993014053",  # Found: Melanie Martinez
    "Jazmin Bean": "1474543013",  # Found: Jazmin Bean
    "Doja Cat": "830588310",  # Found: Doja Cat
    "Rihanna": "63346553",  # Found: Rihanna
    "Cardi B": "956078923",  # Found: Cardi B
    "Miley Cyrus": "137057909",  # Found: Miley Cyrus
    "Sabrina Carpenter": "390647681",  # Found: Sabrina Carpenter
    "Kesha": "334854763",  # Found: Kesha
    "Kylie Minogue": "465031",  # Found: Kylie Minogue
    "Fergie": "151910203",  # Found: Fergie
    "Christina Aguilera": "259398",  # Found: Christina Aguilera
    "Ariana Grande": "412778295",  # Found: Ariana Grande
    "Dua Lipa": "1031397873",  # Found: Dua Lipa
    "Katy Perry": "64387566",  # Found: Katy Perry
    "Taylor Swift": "159260351",  # Found: Taylor Swift
    "Billie Eilish": "1065981054",  # Found: Billie Eilish
    "Selena Gomez": "280215834",  # Found: Selena Gomez
    "Demi Lovato": "280215821",  # Found: Demi Lovato
    "Nicki Minaj": "278464538",  # Found: Nicki Minaj
    "Halsey": "324916925",  # Found: Halsey
    "Camila Cabello": "935727853",  # Found: Camila Cabello
    "Zara Larsson": "570372593",  # Found: Zara Larsson
    "Frank Ocean": "442122051",  # Found: Frank Ocean
    "The Weeknd": "479756766",  # Found: The Weeknd
    "Lana Del Rey": "464296584",  # Found: Lana Del Rey
    "Kendrick Lamar": "368183298",  # Found: Kendrick Lamar
    "Charli XCX": "432942256",  # Found: Charli xcx
    "Rosalía": "313845115",  # Found: ROSALÍA
    "Addison Rae": "1513956049",  # Found: Addison Rae
    "Olivia Rodrigo": "979458609",  # Found: Olivia Rodrigo
    "Chappell Roan": "1264818718",  # Found: Chappell Roan
    "SZA": "605800394",  # Found: SZA
    "Tate McRae": "1446365464",  # Found: Tate McRae
    "Lorde": "602767352",  # Found: Lorde
    "Tyler, The Creator": "420368335",  # Found: Tyler, The Creator
    "A$AP Rocky": "481488005",  # Found: A$AP Rocky
    "Drake": "271256",  # Found: Drake
    "Travis Scott": "549236696",  # Found: Travis Scott
    "Beyoncé": "1419227",  # Found: Beyoncé
    "Madonna": "20044",  # Found: Madonna
    "Megan Thee Stallion": "1258989914",  # Found: Megan Thee Stallion
    "CupcakKe": "1048655899",  # Found: cupcakKe
    "Playboi Carti": "982372505",  # Found: Playboi Carti
    "Mariah Carey": "91853",  # Found: Mariah Carey
}

def clean_database_safe():
    print("[INFO] Curat baza de date (Tabelul 'products')...")
    with app.app_context():
        try:
            db.session.execute(text("TRUNCATE TABLE products RESTART IDENTITY CASCADE;"))
            db.session.commit()
            print("[OK] Tabelul 'products' a fost golit complet si ID-urile resetate.")
        except Exception as e:
            print(f"[WARN] Eroare la TRUNCATE: {e}")
            db.session.rollback()
            try:
                db.session.execute(text("DELETE FROM products;"))
                db.session.commit()
                print("[OK] Tabelul 'products' a fost golit (DELETE).")
            except Exception as e2:
                print(f"[ERROR] Eroare critica: {e2}")

def get_price_cd():
    # Intre 40.99 si 100.99 (ca sa includa si 100)
    base = random.randint(40, 100)
    return float(f"{base}.99")

def get_price_vinyl():
    # Intre 100.99 si 300.99
    base = random.randint(100, 300)
    return float(f"{base}.99")

def import_data():
    with app.app_context():
        clean_database_safe()
        
        print("\n[START] Incepem importul COMPLET (Metoda ID Catalog)...")

        for artist_name, artist_id in ARTIST_IDS.items():
            print(f"\n------------------------------------------------")
            print(f"[INFO] Descarc catalogul pentru: {artist_name} (ID: {artist_id})...")

            # 1. Cerem TOATE albumele asociate acestui ID
            # Folosim 'lookup' in loc de 'search' pentru precizie maxima
            lookup_url = f"https://itunes.apple.com/lookup?id={artist_id}&entity=album&limit=200"
            
            try:
                resp = requests.get(lookup_url).json()
            except Exception as e:
                print(f"[ERROR] Eroare conexiune: {e}")
                continue

            # Rezultatul 0 este artistul, restul sunt albumele
            if resp['resultCount'] < 2:
                print("[WARN] Nu am gasit albume.")
                continue

            # Excludem primul rezultat (info artist) si luam doar albumele
            all_albums = resp['results'][1:]
            
            # Sortam descrescator dupa data
            all_albums.sort(key=lambda x: x.get('releaseDate', ''), reverse=True)

            print(f"[INFO] Gasite {len(all_albums)} intrari in total.")

            seen_exact_titles = set()
            added_count = 0

            for album in all_albums:
                title = album['collectionName']
                
                # --- FILTRE MINIME ---
                # Excludem doar ce nu e muzica relevanta
                forbidden = ["karaoke", "tribute", "instrumental", "commentary", "interview"]
                if any(x in title.lower() for x in forbidden):
                    continue
                
                # Nu mai taiem titlul la paranteza! 
                # Daca e "Britney Jean (Deluxe)", il luam asa cum e.
                # Doar daca e EXACT acelasi titlu il sarim (ex: duplicate de regiune)
                if title in seen_exact_titles:
                    continue
                seen_exact_titles.add(title)

                # 2. Luam piesele pentru album
                collection_id = album['collectionId']
                details_url = f"https://itunes.apple.com/lookup?id={collection_id}&entity=song"
                
                try:
                    details = requests.get(details_url).json()
                except:
                    continue
                
                items = details.get('results', [])
                tracks = [i for i in items if i.get('wrapperType') == 'track']

                # Ignoram single-urile (sub 4 piese)
                if len(tracks) < 4:
                    continue

                # Cautam audio
                audio_url = None
                track_names = []
                for idx, t in enumerate(tracks, 1):
                    track_names.append(f"{idx}. {t['trackName']}")
                    if not audio_url and t.get('previewUrl'):
                        audio_url = t['previewUrl']
                
                if not audio_url:
                    continue

                # --- PREPARARE DATE ---
                # Imagine HQ
                image_url = album.get('artworkUrl100', '').replace('100x100', '600x600')
                release_date = album.get('releaseDate', '')[:10]
                genre = album.get('primaryGenreName', 'Pop')

                # LISTA COMPLETA DE PIESE (fara limitare)
                track_str = "\n".join(track_names)
                
                description = f"Album: {title}\nArtist: {artist_name}\nGen: {genre}\nLansat: {release_date}\n\nLista piese:\n{track_str}"

                # --- ADAUGARE IN DB ---
                try:
                    # CD
                    p_cd = Product(
                        title=title,
                        artist=artist_name,
                        category='CD',
                        price=get_price_cd(),
                        stock=random.randint(5, 50),
                        image_url=image_url,
                        audio_url=audio_url,
                        description=description
                    )
                    db.session.add(p_cd)
                    
                    # Vinyl (50% sansa)
                    if random.choice([True, False]):
                        p_vinyl = Product(
                            title=f"{title} (Vinyl)",
                            artist=artist_name,
                            category='Vinyl',
                            price=get_price_vinyl(),
                            stock=random.randint(2, 10),
                            image_url=image_url,
                            audio_url=audio_url,
                            description=f"Format: Vinyl LP.\n{description}"
                        )
                        db.session.add(p_vinyl)

                    added_count += 1
                    print(f"   [OK] Adaugat: {title}")

                except Exception as e:
                    print(f"   [ERROR] SQL: {e}")

            db.session.commit()
            print(f"[DONE] {artist_name}: {added_count} albume procesate.")

if __name__ == '__main__':
    import_data()