from app import app, db
from models import User, Product

def seed_database():
    """Seed the database with initial admin user and demo products"""
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@music.com',
            role='admin'
        )
        admin.set_password('password')
        db.session.add(admin)
        
        # Create demo products
        products = [
            Product(
                    title='Glory',
                    artist='Britney Spears',
                    price=149.99,
                    stock=10,
                    category='Vinyl',
                    image_url='https://is1-ssl.mzstatic.com/image/thumb/Video211/v4/61/ab/cd/61abcddc-4ff8-9fd4-332b-4a7d332567e0/Job47954b9a-e88f-4a2e-956e-568f9e8120fb-192599192-PreviewImage_Preview_Image_Intermediate_nonvideo_sdr_377254272_2162892720-Time1747333169148.png/592x592bb.webp'
                ),
                Product(
                    title='Artpop',
                    artist='Lady Gaga',
                    price=59.99,
                    stock=15,
                    category='CD',
                    image_url='https://is1-ssl.mzstatic.com/image/thumb/Music125/v4/0c/33/64/0c336478-aaa9-95dc-d373-f6fb8510b170/13UAAIM69752.rgb.jpg/592x592bb.webp'
                ),
                Product(
                    title='Crybaby Perfume',
                    artist='Melanie Martinez',
                    price=499.99,
                    stock=50,
                    category='Merch',
                    image_url='https://images-cdn.ubuy.com.mx/https://images-cdn.ubuy.com.mx/64018eb987089977e7429bb3-cry-baby-perfume-milk-2-5-oz-bottle.jpg64018eb987089977e7429bb3-cry-baby-perfume-milk-2-5-oz-bottle.jpg'
                )
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        print("Database seeded successfully!")
        print("Admin account: admin@music.com / password")

if __name__ == '__main__':
    seed_database()
