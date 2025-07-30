from flask_sqlalchemy import SQLAlchemy
from app import app
from werkzeug.security import generate_password_hash
from datetime import datetime

db = SQLAlchemy(app)

class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(32), unique=True, nullable=False)
        name = db.Column(db.String(64), nullable=False)
        is_admin = db.Column(db.Boolean,nullable=False, default=False)
        is_author = db.Column(db.Boolean,nullable=False, default=False)
        passhash = db.Column(db.String(256), nullable=False)
        email = db.Column(db.String(128), nullable=True)
        bio = db.Column(db.String(256), nullable=True)
        role = db.Column(db.String(16), nullable=False, default='User')
        books_requested = db.Column(db.Integer, nullable=True, default=0)
        date_upgraded = db.Column(db.DateTime, nullable=True)
        date_joined = db.Column(db.DateTime, nullable=False, default=datetime.now())
        is_dark = db.Column(db.Boolean, nullable=False, default=False)

        books = db.relationship('BookAccess', back_populates='user', lazy=True, cascade='all, delete-orphan')
        author_books = db.relationship('author_book', backref='user', lazy=True, cascade='all, delete-orphan')
        reviews = db.relationship('review', backref='user', lazy=True, cascade='all, delete-orphan')
        blacklists = db.relationship('blacklist', backref='user', lazy=True, cascade='all, delete-orphan')
        carts = db.relationship('cart', backref='user', lazy=True, cascade='all, delete-orphan')
        wishlists = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
        favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')

class Section(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(32), unique=True, nullable=False)
        desc = db.Column(db.String(256), nullable=True)
        date_created = db.Column(db.DateTime, nullable=False)
        
        books = db.relationship('book', backref='Section', lazy=True, cascade='all, delete-orphan')

class book(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(64), nullable=False)
        author = db.Column(db.String(64), nullable=False)
        section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
        subsections = db.Column(db.String(64), nullable=True)
        publisher = db.Column(db.String(64), nullable=True)
        date_added = db.Column(db.DateTime, nullable=False)
        pages = db.Column(db.Integer, nullable=True)
        volumne = db.Column(db.Integer, nullable=True)
        desc = db.Column(db.String(256), nullable=True)
        price = db.Column(db.Float, nullable=True)
        book_image = db.Column(db.String(256), nullable=True)
        is_audible = db.Column(db.Boolean, nullable=False, default=False)
        content = db.Column(db.String(5096), nullable=True)
        is_upcoming = db.Column(db.Boolean, nullable=False, default=False)
        book_link = db.Column(db.String(512), nullable=True)
        avail= db.Column(db.DateTime, nullable=True)

        access = db.relationship('BookAccess', back_populates='book', lazy=True, cascade='all, delete-orphan')
        carts = db.relationship('cart', backref='book', lazy=True, cascade='all, delete-orphan')
        reviews = db.relationship('review', backref='book', lazy=True, cascade='all, delete-orphan')
        orders = db.relationship('Order', backref='book', lazy=True, cascade='all, delete-orphan')
        wishlist = db.relationship('Wishlist', backref='book', lazy=True, cascade='all, delete-orphan')
        favorite = db.relationship('Favorite', backref='book', lazy=True, cascade='all, delete-orphan')


class review(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        review = db.Column(db.String(256), nullable=True)
        ratings = db.Column(db.Integer, nullable=True, default=0.0)
        date_created = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
        reviews_count = db.Column(db.Integer, nullable=True, default=0)
        is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
        is_rated= db.Column(db.Boolean, nullable=False, default=False)
        is_reviewed= db.Column(db.Boolean, nullable=False, default=False)
        is_edited= db.Column(db.Boolean, nullable=False, default=False)


class cart(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        price = db.Column(db.Float, nullable=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)
    trans_details = db.Column(db.String(256), nullable=True)

    orders = db.relationship('Order', backref='transaction', lazy=True, cascade='all, delete-orphan')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)


class Wishlist(db.Model):
        id= db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
        date_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        is_wished = db.Column(db.Boolean, nullable=False, default=False)

class Favorite(db.Model):
        id= db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
        is_favourite = db.Column(db.Boolean, nullable=False, default=False)

class BookAccess(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
        granted_at = db.Column(db.DateTime, nullable=True)
        revoked_at = db.Column(db.DateTime, nullable=True)
        isgranted = db.Column(db.Boolean, nullable=False, default=False)
        isrevoked = db.Column(db.Boolean, nullable=False, default=False)
        isrejected = db.Column(db.Boolean, nullable=False, default=False)
        isrequested = db.Column(db.Boolean, nullable=False, default=False)
        request_days = db.Column(db.Integer, nullable=True)
        requested_at = db.Column(db.DateTime, nullable=False, default = datetime.now())

        user = db.relationship('User', back_populates='books')
        book = db.relationship('book', back_populates='access')

class author_book(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        title = db.Column(db.String(64), nullable=False)
        sections = db.Column(db.String(64), nullable=True)
        subsections = db.Column(db.String(64), nullable=True)
        publisher = db.Column(db.String(64), nullable=True)
        pages = db.Column(db.Integer, nullable=True)
        volumne = db.Column(db.Integer, nullable=True)
        desc = db.Column(db.String(256), nullable=True)
        price = db.Column(db.Float, nullable=True)
        book_image = db.Column(db.String(256), nullable=True)
        is_audible = db.Column(db.Boolean, nullable=False, default=False)
        content = db.Column(db.String(5096), nullable=True)
        book_link = db.Column(db.String(512), nullable=True)
        is_suggested = db.Column(db.Boolean, nullable=False, default=False)
        is_rejected = db.Column(db.Boolean, nullable=False, default=False)

class blacklist(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        blacklisted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
        is_blacklisted = db.Column(db.Boolean, nullable=False, default=False)
        blacklisted_till = db.Column(db.DateTime, nullable=True)
        reason = db.Column(db.String(128), nullable=True)      




with app.app_context():
    db.create_all()
    # if admin exists, else create admin
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        password_hash = generate_password_hash('admin')
        admin = User(username='admin', passhash=password_hash, name='Admin', is_admin=True, email='admin@librarystories.com', role="ADMINISTRATOR", bio="Admin of Library-Stories")
        suser = User(username='suser', passhash=password_hash, name='Sample User', is_admin=False,email='sampleuser@user.com', role="User", bio="USER of Library-Stories", date_joined=datetime.now())
        sauthor = User(username='sauthor', passhash=password_hash, name='Sample Author', is_admin=False,is_author=True, email='sampleauthor@author.com', role="AUTHOR", bio="AUTHOR of Library-Stories", date_upgraded=datetime.now(),  date_joined=datetime.now())        
        db.session.add(admin)
        db.session.add(suser)
        db.session.add(sauthor)
        db.session.commit()