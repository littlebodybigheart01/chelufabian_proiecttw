"""Database initialization script with automatic seeding."""
from app import app, db
from models import User, Product

def init_database():
    """Initialize database with tables and demo data."""
    with app.app_context():
        db.create_all()
        
        admin_exists = User.query.filter_by(username='admin').first()
        if not admin_exists:
            admin = User(
                username='admin',
                email='admin@music.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin@music.com / admin123")
        
        if Product.query.count() == 0:
            demo_products = [
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
            db.session.add_all(demo_products)
            db.session.commit()
            print("Demo products added")
        
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()
