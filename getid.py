import requests
import time

# Lista ta de artisti
ARTISTS = [
    "Britney Spears", "Lady Gaga", "Melanie Martinez", "Jazmin Bean",
    "Doja Cat", "Rihanna", "Cardi B", "Miley Cyrus",
    "Sabrina Carpenter", "Kesha", "Kylie Minogue", "Fergie",
    "Christina Aguilera", "Ariana Grande", "Dua Lipa", "Katy Perry",
    "Taylor Swift", "Billie Eilish", "Selena Gomez", "Demi Lovato",
    "Nicki Minaj", "Halsey", "Camila Cabello", "Zara Larsson",
    "Frank Ocean", "The Weeknd", "Lana Del Rey", "Kendrick Lamar",
    "Charli XCX", "Rosalía", "Addison Rae", "Olivia Rodrigo",
    "Chappell Roan", "SZA", "Tate McRae", "Lorde",
    "Tyler, The Creator", "A$AP Rocky", "Drake", "Travis Scott",
    "Beyoncé", "Madonna", "Megan Thee Stallion", "CupcakKe",
    "Playboi Carti", "Mariah Carey"
]

def fetch_ids():
    print("GENERATING ARTIST MAP...\n")
    print("ARTIST_IDS = {")
    
    for artist in ARTISTS:
        try:
            url = "https://itunes.apple.com/search"
            params = {
                "term": artist,
                "entity": "musicArtist",
                "limit": 1,
                "attribute": "artistTerm"
            }
            resp = requests.get(url, params=params).json()
            
            if resp['resultCount'] > 0:
                data = resp['results'][0]
                artist_name = data['artistName']
                artist_id = data['artistId']
                # Printam formatat direct pentru Python
                print(f'    "{artist}": "{artist_id}",  # Found: {artist_name}')
            else:
                print(f'    # "{artist}": "NOT_FOUND",')
                
        except Exception as e:
            print(f'    # Error for {artist}: {e}')
            
        # Pauza mica sa nu primim block
        time.sleep(0.2)

    print("}")
    print("\n\nCOPIAZA CODUL DINTRE ACOLADE IN SCRIPTUL FINAL!")

if __name__ == "__main__":
    fetch_ids()