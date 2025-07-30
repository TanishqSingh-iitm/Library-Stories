from flask import render_template, request, redirect, url_for, session, flash, send_file
from app import app
from models import User, Section, book, review, BookAccess, Order, cart, Transaction, Wishlist, Favorite, author_book, blacklist, db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from datetime import datetime, timedelta
import csv
from uuid import uuid4
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import textwrap
from io import BytesIO
import matplotlib.pyplot as plt


  # For Text to Speech Functionality
from gtts import gTTS
import os
def text_to_mp3(text):
        audio = gTTS(text, lang='en')
        audio.save('static/audio/book.mp3')
        

  # For Automatic Revoke of Book Access
def revoke_access_blacklist():
    requests = BookAccess.query.filter_by(isgranted=True).all()
    Blacklist = blacklist.query.filter_by(is_blacklisted=True).all()
    now = datetime.now()
    for request in requests:
        if request.revoked_at <= now:
            request.isgranted = False
            request.isrevoked = True
            request.isrequested = False
    for black in Blacklist:
        if black.blacklisted_till <= now:
            db.session.delete(black)
    db.session.commit()


# Login and Registration Portals Routes
 
@app.route('/login')
def login():
    return render_template('logins/login.html')


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please Enter data in all fields')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username = username).first()

    if not user:
        flash('Username does not exist')
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash, password):
        flash('Pasword is Incorrect')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id
    revoke_access_blacklist()


    flash("Login Successful")
    return redirect(url_for('index'))

@app.route('/terms&policy')
def terms():
    return render_template('logins/terms&policy.html')

@app.route('/register')
def register():
    return render_template('logins/register.html')

@app.route('/register', methods=['POST'])
def register_post():
     username = request.form.get('username')
     password = request.form.get('password')
     confirm_password = request.form.get('confirm_password')
     name = request.form.get('name')    
     email = request.form.get('email')
     isterms = request.form.get('isterms')

     if not username or not password or not confirm_password or not name:
           flash('Please Enter data in all required fields')
           return redirect(url_for('register'))
     
     if password != confirm_password:
         flash('Passwords do not match')
         return redirect(url_for('register'))
     
     if User.query.filter_by(username=username).first():
         flash("Username already Taken, Kindly choose another")
         return redirect(url_for('register'))
     if isterms != 'on':
         flash('Please Agree to Terms and Conditions!')
         return redirect(url_for('register'))

     joining =  datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"),"%Y-%m-%d %H:%M")

     password_hash = generate_password_hash(password)
     new_user = User(username=username, passhash=password_hash, name=name, email=email, role="User", date_joined=joining, bio="No Bio Available Yet")
     db.session.add(new_user)
     db.session.commit()
     flash('Registration Successful')
     return redirect(url_for('login'))


@app.route('/profile/deleteaccount')
def userdelete():
    return render_template('profile/delete.html',user=current_user())


@app.route('/profile/deleteaccount', methods=['POST'])
def userdelete_post():
    password = request.form.get('pass')
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, password):
        flash('Incorrect Password! Account Deletion Failed')
        return redirect(url_for('profile'))
    db.session.delete(user)
    db.session.commit()
    session.pop('user_id')
    flash('Account Deleted Successfully')
    return redirect(url_for('login'))


# Authentications and Logout Functions

def auth_Required(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please Login to Continue')
            return redirect(url_for('login'))
    return inner

def admin_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please Login to Continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_admin:
            flash('You do not have the required permission to access this page')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return inner

def author_required(f):
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please Login to Continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.is_author:
            flash('You do not have the required permission to access this page')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return inner

@app.route('/logout')
@auth_Required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))


#  current User query for session
def current_user():
        user0 = User.query.get(session['user_id'])
        return user0

#  Profile page routes

@app.route('/profile', methods=['GET'])
@auth_Required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile/profile.html',user=user)

@app.route('/editprofile')
@auth_Required
def editprofile():
    user = User.query.get(session['user_id'])
    return render_template('profile/editprofile.html',user=user)

@app.route('/editprofile', methods=['POST'])
@auth_Required
def editprofile_post():
    username = request.form.get('username')
    cpassword = request.form.get('cpassword')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    name = request.form.get('name')
    bio = request.form.get('bio')
    email = request.form.get('email')

    if not username or not cpassword or not password or not confirm_password or not name:
        flash('Please fill out all the required fields')
        return redirect(url_for('editprofile'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('editprofile'))
    
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('editprofile'))
    
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.name = name
    user.bio = bio
    user.email = email
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('profile'))


# admin routes

@app.route('/admin')
@admin_required
def admin():
    sections = Section.query.all()
    return render_template('admin/admin.html', user=current_user(), sections=sections)

# Admin Book Section Routes

# Adding Sections

@app.route('/section/add')
@admin_required
def add_section():
    return render_template('section/add.html',user=current_user())

@app.route('/section/add', methods=['POST'])
@admin_required
def add_section_post():
    name = request.form.get('name')
    desc = request.form.get('desc')

    if not name:
        flash('Please fill out Required fields')
        return redirect(url_for('add_section'))
    if not desc:
        desc = "No Description Available"

    daten = datetime.now().strftime("%Y-%m-%d %H:%M")
    datec = datetime.strptime(daten,"%Y-%m-%d %H:%M")
    
    section = Section(name=name,desc=desc,date_created=datec)
    
    db.session.add(section)
    db.session.commit()

    flash('Section added successfully')
    return redirect(url_for('admin'))

# Deleting Sections

@app.route('/section/<int:id>/delete')
@admin_required
def delete_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/delete.html',user=current_user(), section=section)

@app.route('/section/<int:id>/delete', methods=['POST'])
@admin_required
def delete_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Category does not exist')
        return redirect(url_for('admin'))
    db.session.delete(section)
    db.session.commit()

    flash('Book Section deleted successfully')
    return redirect(url_for('admin'))

# Editing Sections

@app.route('/section/<int:id>/edit')
@admin_required
def edit_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/edit.html',user=current_user(), section=section)

@app.route('/section/<int:id>/edit', methods=['POST'])
@admin_required
def edit_section_post(id):
    section = Section.query.get(id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))
    name = request.form.get('name')
    desc = request.form.get('desc')
    if not name:
        flash('Please fill out all fields')
        return redirect(url_for('edit_section', id=id))
    if not desc:
         desc = "No Description Available"
    section.name = name
    section.desc = desc
    db.session.commit()
    flash('Book Section updated successfully')
    return redirect(url_for('admin'))

# Showing Sections

@app.route('/section/<int:id>/')
@admin_required
def show_section(id):
    section = Section.query.get(id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))
    return render_template('section/show.html', section=section, user=current_user())



# Book Routes

# Adding Books

@app.route('/book/add/<int:section_id>')
@admin_required
def add_book(section_id):
    sections = Section.query.all()
    section = Section.query.get(section_id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))
    now = datetime.now().strftime('%Y-%m-%d')
    return render_template('book/add.html', section=section, sections=sections, now=now, user=current_user())

@app.route('/book/add/', methods=['POST'])
@admin_required
def add_book_post():
    title = request.form.get('name')
    pub = request.form.get('publisher')
    auth = request.form.get('author')
    desc = request.form.get('desc')
    ssec = request.form.get('ssec')
    pages = request.form.get('pages')
    volume = request.form.get('volume')
    price = request.form.get('price')
    bkimg = request.form.get('bookimg')
    section_id = request.form.get('section_id')
    content = request.form.get('content')
    availdate = request.form.get('availdate')
    isaudible = request.form.get('isaudi')
    link = request.form.get('link')
        
    section = Section.query.get(section_id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))

    if not title or not price or not auth or not availdate:
        flash('Please Fill out all Required Fields')
        return redirect(url_for('add_book', section_id=section_id))
    try:
        price = float(price)
        availdate = datetime.strptime(availdate, '%Y-%m-%d')
    
    except ValueError:
        flash('Invalid Book Price Please set Correct One')
        return redirect(url_for('add_book', section_id=section_id))

    if price < 0:
        flash('Invalid Book Price')
        return redirect(url_for('add_book', section_id=section_id))
    
    iscoming = False
    if availdate > datetime.now():
        iscoming = True
    
    if availdate < datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d"):
        flash('Invalid Book Available Date')
        return redirect(url_for('add_book', section_id=section_id))

    if not desc:
        desc = "No Description Available"
    if not ssec:
        ssec = "No Sub-sections Available"
    if not pages:
        pages = 0
    if not volume:
        volume = 0
    if not pub:
        pub = "No Book Publisher Available"
    if isaudible == 'on':
        if not content:
            flash("IF Book is Audible Then Content Cannot be Empty")
            return redirect(url_for('add_book', section_id=section_id))
        
        isaudible = True
    else:
        isaudible = False
    
    if not ssec:
        ssec = "None"
    
    adddate = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")
    availdate = datetime.strptime(availdate.strftime("%Y-%m-%d"), "%Y-%m-%d")
    
    Book = book(title=title, price=price,book_link=link,avail=availdate, section_id=section_id, desc=desc, author=auth, publisher=pub, pages=pages, volumne=volume, book_image=bkimg, content=content, is_audible=isaudible, is_upcoming=iscoming, date_added=adddate,subsections=ssec)
    db.session.add(Book)
    db.session.commit()

    flash('Book added successfully')
    return redirect(url_for('show_section', id=section_id))

# Editing Books

@app.route('/book/<int:id>/edit')
@admin_required
def edit_book(id):
    sections = Section.query.all()
    Books = book.query.get(id)
    now = datetime.now().strftime('%Y-%m-%d')
    return render_template('book/edit.html', section=sections,now=now, book=Books, user=current_user())

@app.route('/book/<int:id>/edit', methods=['POST'])
@admin_required
def edit_book_post(id):
    title = request.form.get('name')
    pub = request.form.get('publisher')
    auth = request.form.get('author')
    desc = request.form.get('desc')
    ssec = request.form.get('ssec')
    pages = request.form.get('pages')
    volume = request.form.get('volume')
    price = request.form.get('price')
    bkimg = request.form.get('bookimg')
    section_id = request.form.get('section_id')
    content = request.form.get('content')
    availdate = request.form.get('availdate')
    isaudible = request.form.get('isaudi')
    link = request.form.get('link')
        
    section = Section.query.get(section_id)
    if not section:
        flash('Book Section does not exist')
        return redirect(url_for('admin'))

    if not title or not price or not auth or not availdate:
        flash('Please Fill out all Required Fields')
        return redirect(url_for('add_book', section_id=section_id))
    try:
        price = float(price)
        availdate = datetime.strptime(availdate, '%Y-%m-%d')
    
    except ValueError:
        flash('Invalid Book Price Please set Correct One')
        return redirect(url_for('add_book', section_id=section_id))

    if price < 0:
        flash('Invalid Book Price')
        return redirect(url_for('add_book', section_id=section_id))
    
    iscoming = False
    if availdate > datetime.now():
        iscoming = True
    
    if availdate < datetime.strptime(datetime.now().strftime("%Y-%m-%d"), "%Y-%m-%d"):
        flash('Invalid Book Available Date')
        return redirect(url_for('add_book', section_id=section_id))

    if not desc:
        desc = "No Description Available"
    if not ssec:
        ssec = "No Sub-sections Available"
    if not pages:
        pages = 0
    if not volume:
        volume = 0
    if not pub:
        pub = "No Book Publisher Available"
    if isaudible == 'on':
        if not content:
            flash("IF Book is Audible Then Content Cannot be Empty")
            return redirect(url_for('edit_book', id=id))
        isaudible = True
    else:
        isaudible = False
    
    availdate = datetime.strptime(availdate.strftime("%Y-%m-%d"), "%Y-%m-%d")

    Book=book.query.get(id)
    Book.title = title
    Book.price = price
    Book.section_id = section_id
    Book.desc = desc
    Book.author = auth
    Book.publisher = pub
    Book.subsections = ssec
    Book.pages = pages
    Book.volumne = volume
    Book.book_image = bkimg
    Book.content = content
    Book.is_audible = isaudible
    Book.is_upcoming = iscoming
    Book.book_link = link
    Book.avail = availdate
    db.session.commit()
    
    flash('Book Edited Successfully')
    return redirect(url_for('show_section', id=section_id))

# Deleting Books

@app.route('/book/<int:id>/delete')
@admin_required
def delete_book(id):
    Book = book.query.get(id)
    if not Book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    return render_template('book/delete.html', book=Book, user=current_user())

@app.route('/book/<int:id>/delete', methods=['POST'])
@admin_required
def delete_book_post(id):
    Book = book.query.get(id)
    if not Book:
        flash('Book does not exist')
        return redirect(url_for('admin'))
    section_id = Book.section_id
    db.session.delete(Book)
    db.session.commit()

    flash('Book deleted successfully')
    return redirect(url_for('show_section', id=section_id))


# Showing Books

# For Admin view

@app.route('/book/<int:id>/show')
@admin_required
def ad_show_book(id):
    Book=book.query.get(id)
    section_id = Book.section_id
    section_name = Section.query.get(section_id).name
    reviews = review.query.filter_by(book_id=id).all()
    users = User.query.all()
    ratings = review.query.all()
    avg=0
    if len(ratings)>0:
        sum = 0;count=0
        for rating in ratings:
                if Book.id == rating.book_id:
                    sum=sum + int(rating.ratings)
                    count+=1
        try:
                avg = sum/count
        except ZeroDivisionError:
                    avg=0


    if not Book:
        flash('Book does not exist')
        return redirect(url_for('show_section'))
    if not section_id:
        flash('Book Section does not exist anymore')
        return redirect(url_for('admin'))
    return render_template('book/show.html',users=users, reviews=reviews, section_name=section_name, book=Book, user=current_user(), overall=avg)



# For Users view

@app.route('/book/<int:id>/view')
@auth_Required
def view_book(id):
    Book=book.query.get(id)
    section_id = Book.section_id
    section_name = Section.query.get(section_id).name
    reviews = review.query.filter_by(book_id=id).all()
    users = User.query.all()
    ratings = review.query.all()
    avg=0
    if len(ratings)>0:
        sum = 0;count=0
        for rating in ratings:
                if Book.id == rating.book_id:
                    sum=sum + int(rating.ratings)
                    count+=1
        try:
                avg = sum/count
        except ZeroDivisionError:
                    avg=0


    if not Book:
        flash('Book does not exist anymore')
        return redirect(url_for('index'))
    if not section_id:
        flash('Book Section does not exist anymore')
        return redirect(url_for('index'))
    return render_template('book/view.html',users=users, reviews=reviews, section_name=section_name, book=Book, user=current_user(),overall=avg)


# User Routes index


@app.route('/')
@app.route('/index')
@auth_Required
def index():
    sections = Section.query.all()
    isupcoming = book.query.filter_by(is_upcoming=True).all()
    newbooks= book.query.filter(book.is_upcoming == False).order_by(book.date_added.desc()).limit(5).all()
    ratings = review.query.all()
    books = book.query.all()
    bestsellers = []
    if len(ratings)>0:
        for Book in books:
            try:
                    sum = 0;count=0
                    for rating in ratings:
                        if Book.id == rating.book_id:
                            sum=sum + int(rating.ratings)
                            count+=1

                    avg = sum / count
                    if (avg > 7.5 and count > 0):
                            bestsellers.append(Book)
            except ZeroDivisionError:
                    avg=0
            
                    
        
        if len(bestsellers) > 10:
            bestsellers = bestsellers[:10]
    session['theme'] = 'dark'
    selected_option = request.args.get('parameter') or ''
    searchpara = request.args.get('searchpara') or ''
    if selected_option == 'price':
        try:
            searchpara = float(searchpara)
            if searchpara < 0:
                flash('Invalid Price Input. Try Again')
                return redirect(url_for('index'))
        
        except ValueError:
            flash('Invalid Price Input. Try Again')
            return redirect(url_for('index'))

    Blacklist = blacklist.query.filter_by(user_id=session['user_id']).first()

    if selected_option == 'ebook':
        searched_Book = searchpara
        ebooks = book.query.filter(book.title.ilike(f'%{searchpara}%')).all()
        ebooks_section_ids = [book.section_id for book in ebooks]
        sections = Section.query.filter(Section.id.in_(ebooks_section_ids)).all()
        return render_template('index.html',bestsellers=bestsellers, user=current_user(), sections=sections,newbooks=newbooks, upcoming_books=isupcoming, searchpara=searchpara, selected_option=selected_option, searched_Book=searched_Book, ebooks=ebooks, blacklisted=Blacklist)


    if selected_option == 'section':
        sections = Section.query.filter(Section.name.ilike(f'%{searchpara}%')).all()
        return render_template('index.html',bestsellers=bestsellers, user=current_user(), sections=sections,newbooks=newbooks, upcoming_books=isupcoming, searchpara=searchpara, selected_option=selected_option, blacklisted=Blacklist)


    if selected_option == 'author':
        searched_author = searchpara
        author_books = book.query.filter(book.author.ilike(f'%{searchpara}%')).all()
        author_books_section_ids = [book.section_id for book in author_books]
        sections = Section.query.filter(Section.id.in_(author_books_section_ids)).all()
        return render_template('index.html',bestsellers=bestsellers, user=current_user(), sections=sections,newbooks=newbooks, upcoming_books=isupcoming, searchpara=searchpara, selected_option=selected_option, searched_author=searched_author,author_books=author_books, blacklisted=Blacklist)


    if selected_option == 'price':
        searched_price = searchpara
        priced_books = book.query.filter(book.price <= searchpara).all()
        priced_books_section_ids = [book.section_id for book in priced_books]
        sections = Section.query.filter(Section.id.in_(priced_books_section_ids)).all()
        return render_template('index.html',bestsellers=bestsellers, user=current_user(), sections=sections,newbooks=newbooks, upcoming_books=isupcoming, searchpara=searchpara, selected_option=selected_option, searched_price=searched_price, priced_books=priced_books, blacklisted=Blacklist)


    if selected_option == 'publisher':
        searched_publisher = searchpara
        pub_books = book.query.filter(book.publisher.ilike(f'%{searchpara}%')).all()
        pub_books_section_ids = [book.section_id for book in pub_books]
        sections = Section.query.filter(Section.id.in_(pub_books_section_ids)).all()
        return render_template('index.html',bestsellers=bestsellers, user=current_user(), sections=sections,newbooks=newbooks, upcoming_books=isupcoming, searchpara=searchpara, selected_option=selected_option, searched_publisher=searched_publisher, pub_books=pub_books, blacklisted=Blacklist)



    return render_template('index.html',bestsellers=bestsellers, user=current_user(), sections=sections,newbooks=newbooks, upcoming_books=isupcoming, searchpara=searchpara, selected_option=selected_option, blacklisted=Blacklist)

@app.route('/toggle-dark-mode')
@auth_Required
def toggle_dark_mode():
    user = User.query.get(session['user_id'])
    if user.is_dark:
        user.is_dark = False
    else:
        user.is_dark = True
    db.session.commit()
    return redirect(url_for('profile'))


# Cart Operations


@app.route('/cart')
@auth_Required
def Cart():
    carts = cart.query.filter_by(user_id=session['user_id']).all()
    sections = Section.query.all()
    total = sum([cart.book.price for cart in carts])
    return render_template('user/cart.html', carts=carts,sections=sections, total=total, user=current_user())


# Add to Cart

@app.route('/add_to_cart/<int:book_id>', methods=['POST'])
@auth_Required
def add_to_cart(book_id):
    Book = book.query.get(book_id)
    if not Book:
        flash('Book does not exist')
        return redirect(url_for('index'))

    if cart.query.filter_by(user_id=session['user_id'], book_id=book_id).first():
        flash('Book already in Cart')
        return redirect(url_for('index'))
    
    Cart = cart(user_id=session['user_id'], book_id=book_id, price=Book.price)
    db.session.add(Cart)

    db.session.commit()

    flash('Book Added to cart successfully')
    return redirect(url_for('index'))


# Remove from Cart

@app.route('/cart/<int:id>/delete', methods=['POST'])
@auth_Required
def delete_cart(id):
    Cart = cart.query.get(id)
    if not Cart:
        flash('Cart does not exist')
        return redirect(url_for('Cart'))
    if Cart.user_id != session['user_id']:
        flash('You are not authorized to Access this page')
        return redirect(url_for('Cart'))
    db.session.delete(Cart)
    db.session.commit()
    flash('Cart Item deleted successfully')
    return redirect(url_for('Cart'))

# Check Out

@app.route('/checkout', methods=['POST'])
@auth_Required
def checkout():
    carts = cart.query.filter_by(user_id=session['user_id']).all()
    if not carts:
        flash('Cart is empty')
        return redirect(url_for('Cart'))

    booksdetails=""
    for Cart in carts:
        sections = Section.query.get(Cart.book.section_id)
        booksdetails = booksdetails + Cart.book.title +"," + Cart.book.author+"," + sections.name + "," + str(Cart.book.price) + "\n"
    transaction = Transaction(user_id=session['user_id'], datetime=datetime.now(),trans_details=booksdetails)
    for Cart in carts:
        order = Order(transaction=transaction, book=Cart.book, price=Cart.book.price)
        db.session.add(order)
        db.session.delete(Cart)
    db.session.add(transaction)
    db.session.commit()

    flash('Order placed successfully')
    return redirect(url_for('orders'))


# Orders and export csv

@app.route('/orders')
def orders():
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
    sections = Section.query.all()
    return render_template('user/orders.html', transactions=transactions, sections=sections, user=current_user())


@app.route('/export_csv')
@auth_Required
def export_csv():
    transactions = Transaction.query.filter_by(user_id=session['user_id']).all()
    filename = uuid4().hex + '.csv'
    url = 'static/csv/' + filename
    with open(url, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Transaction_id', 'datetime', 'Book title', 'Book Author','Book Section', 'Book price'])
        for transaction in transactions:
            items = transaction.trans_details.split(',')
            writer.writerow([transaction.id,transaction.datetime,items[0],items[1],items[2],items[3]])
    flash('CSV file exported successfully')
    return redirect(url_for('static', filename='csv/'+filename))


# User Borrow Book


@app.route('/borrow/<int:id>')
@auth_Required
def borrow(id):
    Book = book.query.get(id)
    if not Book:
        flash('Book does not exist')
        return redirect(url_for('index'))
    sections = Section.query.get(Book.section_id)
    return render_template('user/borrow.html', books=Book, sections=sections, user=current_user())


@app.route('/borrow/<int:id>', methods=['POST'])
@auth_Required
def borrow_post(id):
    Book = book.query.get(id)
    if not Book:
        flash('Book does not exist')
        return redirect(url_for('index'))
    sections = Section.query.get(Book.section_id)
    if not sections:
        flash('Book Section does not exist')
        return redirect(url_for('index'))
    
    days = request.form.get('bookborrow')
    
    if not days:
        flash('Please Enter No of Days to Borrow Book')
        return redirect(url_for('borrow', id=id))
    

    requested=True
    now = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")
    
    if BookAccess.query.filter_by(user_id=session['user_id'], book_id=id, isrequested=True).first():
        flash('Book already requested')
        return redirect(url_for('index'))
    
    count = BookAccess.query.filter_by(user_id=session['user_id'], isgranted=True, isrequested=True).count()
    
    
    user = User.query.get(session['user_id'])
    if user.role == "User":
         if count >= 5:
            flash('You have reached the maximum limit of Books to Borrow')
            return redirect(url_for('index'))
    if user.role == "AUTHOR":
         if count >= 10:
            flash('You have reached the maximum limit of Books to Borrow')
            return redirect(url_for('index'))
    
    bookaccess = BookAccess(user_id=current_user().id, book_id = id, request_days=days, isrequested=requested, requested_at=now)
    db.session.add(bookaccess)
    db.session.commit()
    
    flash("Book Requested Successfully, Please Wait for Approval")
    return redirect(url_for('index'))


# Admin Approvals 


@app.route('/admin/approvals')
@admin_required
def approvals():
    requests = BookAccess.query.filter_by(isrequested=True).all()
    sections = Section.query.all()
    Book=book.query.all()
    Users = User.query.all()
    count = BookAccess.query.filter_by(isgranted=True, isrequested=True).count()
    counts = BookAccess.query.filter_by(isgranted=False, isrequested=True).count()
    
    return render_template('admin/approval.html',books=Book, sections=sections,users=Users ,requests=requests, user=current_user(),counts=counts,countss=count)


@app.route('/admin/approvals/<int:request_id>/grant', methods=['POST'])
@admin_required
def approvals_post_grant(request_id):
    requests = BookAccess.query.get(request_id)

    if not requests.book_id:
        flash('Book does not exist anymore')
        return redirect(url_for('approvals'))
    
    if not requests.user_id:
        flash('User does not exist anymore')
        return redirect(url_for('approvals'))
    
    if not requests.isrequested:
        flash('Book Request does not exist anymore')
        return redirect(url_for('approvals'))
    if requests.isgranted:
        flash('Book is Already Granted')
        return redirect(url_for('approvals'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    due = datetime.strptime(now, '%Y-%m-%d %H:%M') + timedelta(days=requests.request_days)
    isgrant = True
    granted = datetime.strptime(now, '%Y-%m-%d %H:%M')
    
    user=User.query.get(requests.user_id)
    user.books_requested += 1

    requests.isgranted = isgrant
    requests.isrequested = True
    requests.granted_at = granted
    requests.revoked_at = due
    db.session.commit()

    flash('Book Request Granted Successfully')
    return redirect(url_for('approvals'))


@app.route('/admin/approvals/<int:request_id>/revoke', methods=['POST'])
@admin_required
def approvals_post_revoke(request_id):
    requests = BookAccess.query.get(request_id)

    if not requests.book_id:
        flash('Book does not exist anymore')
        return redirect(url_for('approvals'))
    
    if not requests.user_id:
        flash('User does not exist anymore')
        return redirect(url_for('approvals'))
    
    if not requests.isgranted:
        flash('Book is not Granted anymore')
        return redirect(url_for('approvals'))

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    now = datetime.strptime(now, '%Y-%m-%d %H:%M')
    isgrant = False
    isrequest = False
    isrevoke = True
    
    user=User.query.get(requests.user_id)
    if user.books_requested > 0:
        user.books_requested -= 1
    else:
        flash('User has no Books to Revoke')
        return redirect(url_for('approvals'))

    requests.isgranted = isgrant
    requests.isrequested = isrequest
    requests.revoked_at = now
    requests.isrevoked = isrevoke
    db.session.commit()

    flash('Book Access Revoked Successfully')
    return redirect(url_for('approvals'))


@app.route('/admin/approvals/<int:request_id>/reject', methods=['POST'])
@admin_required
def approvals_post_reject(request_id):
    requests = BookAccess.query.get(request_id)

    if not requests.book_id:
        flash('Book does not exist anymore')
        return redirect(url_for('approvals'))
    
    if not requests.user_id:
        flash('User does not exist anymore')
        return redirect(url_for('approvals'))
    
    if requests.isrejected:
        flash('Book is Already Rejected')
        return redirect(url_for('approvals'))
    
    if requests.isrevoked:
        flash('Book Access is Already Revoked')
        return redirect(url_for('approvals'))


    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    now = datetime.strptime(now, '%Y-%m-%d %H:%M')
    isgrant = False
    isrequest = False
    isrevoke = False
    isreject = True
    
    requests.isgranted = isgrant
    requests.isrequested = isrequest
    requests.isrejected = isreject
    requests.isrevoked = isrevoke
    requests.revoked_at = now
    db.session.commit()

    flash('Book Request Rejected Successfully')
    return redirect(url_for('approvals'))


# User mybooks routes

@app.route('/mybooks')
@auth_Required
def mybooks():
    requests = BookAccess.query.filter_by(user_id=session['user_id']).all()
    books=book.query.all()
    sections = Section.query.all()
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
    count = BookAccess.query.filter_by(user_id=session['user_id'], isgranted=False, isrevoked=False, isrequested=True, isrejected=False).count()
    counts = BookAccess.query.filter_by(user_id=session['user_id'], isgranted=True, isrevoked=False, isrequested=True, isrejected=False).count()

    return render_template('user/mybooks.html',transactions=transactions, requests=requests, books=books, sections=sections, user=current_user(), counts=count, countss=counts)


@app.route('/mybooks/<int:request_id>/cancel')
@auth_Required
def cancel(request_id):
    requests = BookAccess.query.get(request_id)
    if not requests:
        flash('Book Request does not exist')
    books = book.query.get(requests.book_id)
    if not books:
        flash('Book does not exist anymore')
        return redirect(url_for('mybooks'))
    if not current_user():
        flash('User does not exist anymore')
        return redirect(url_for('login'))
    
    return render_template('user/cancel.html',book=books, requests=requests, user=current_user())


@app.route('/mybooks/<int:request_id>/cancel', methods=['POST'])
@auth_Required
def cancel_post(request_id):
    requests = BookAccess.query.get(request_id)
    if not requests:
        flash('Book Request does not exist')
    books = book.query.get(requests.book_id)
    if not books:
        flash('Book does not exist anymore')
        return redirect(url_for('mybooks'))
    if not current_user():
        flash('User does not exist anymore')
        return redirect(url_for('login'))
    isgrant = False
    isrequest = False
    isrevoke = False
    isreject = False
    requests.isgranted = isgrant
    requests.isrequested = isrequest
    requests.isrejected = isreject
    requests.isrevoked = isrevoke
    db.session.commit()

    flash('Book Request Cancelled Successfully')
    return redirect(url_for('mybooks'))


@app.route('/mybooks/<int:request_id>/return')
@auth_Required
def return_get(request_id):
    requests = BookAccess.query.get(request_id)
    books = book.query.get(requests.book_id)
    if not requests:
        flash('Book Request does not exist')
        return redirect(url_for('mybooks'))
    if not books:
        flash('Book does not exist anymore')
        return redirect(url_for('mybooks'))
    if not current_user():
        flash('User does not exist anymore')
        return redirect(url_for('login'))
    return render_template('user/return.html',book=books, requests=requests, user=current_user())

@app.route('/mybooks/<int:request_id>/return', methods=['POST'])
@auth_Required
def return_post(request_id):
    requests = BookAccess.query.get(request_id)
    books = book.query.get(requests.book_id)
    if not requests:
        flash('Book Request does not exist')
        return redirect(url_for('mybooks'))
    if not books:
        flash('Book does not exist anymore')
        return redirect(url_for('mybooks'))
    if not current_user():
        flash('User does not exist anymore')
        return redirect(url_for('login'))
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    now = datetime.strptime(now, '%Y-%m-%d %H:%M')
    isgrant = False
    isrequest = False
    isrevoke = False
    isreject = False
    requests.isgranted = isgrant
    requests.isrequested = isrequest
    requests.isrejected = isreject
    requests.isrevoked = isrevoke
    requests.revoked_at = now
    db.session.commit()
    flash('Book Returned Successfully')
    return redirect(url_for('mybooks'))


@app.route('/mybooks/<int:request_id>/read')
@auth_Required
def read_listen(request_id):
    requests = BookAccess.query.get(request_id)
    if not requests:
        flash('Book Request does not exist')
        return redirect(url_for('mybooks'))
    books = book.query.get(requests.book_id)
    if not books:
        flash('Book does not exist anymore')
        return redirect(url_for('mybooks'))
    sections = Section.query.get(books.section_id)
    if not sections:
        flash('Book Section does not exist anymore')
        return redirect(url_for('mybooks'))
    
    if not books.book_link:
        if books.content:
            contents = books.content
            text_to_mp3(contents)
    else:
        return redirect(books.book_link)


    return render_template('book/read.html',books=books,sections=sections, requests=requests, user=current_user())


        # Review Routes

@app.route('/mybooks/<int:request_id>/review')
@auth_Required
def Review(request_id):
    requests = BookAccess.query.get(request_id)
    if not requests:
        flash('Book Request does not exist')
    books = book.query.get(requests.book_id)
    sections = Section.query.get(books.section_id)

    return render_template('review/Review.html',books=books,sections=sections, requests=requests, user=current_user())


@app.route('/mybooks/<int:request_id>/review', methods=['POST'])
@auth_Required
def Review_post(request_id):
    requests = BookAccess.query.get(request_id)
    if not requests:
        flash('Book Request does not exist')
    books = book.query.get(requests.book_id)
    sections = Section.query.get(books.section_id)
    if not books:
        flash('Book does not exist anymore')
        return redirect(url_for('mybooks'))
    if not sections:
        flash('Book Section does not exist anymore')
        return redirect(url_for('mybooks'))
    if not current_user():
        flash('User does not exist anymore')
        return redirect(url_for('login'))
    
    reviewss = review.query.filter_by(user_id=session['user_id']).count()
    if reviewss > 2:
        flash('You have reached the maximum limit of Reviews')
        return redirect(url_for('mybooks'))
    counts= reviewss
    if counts==0:
        count=1
    else:
        count=counts+1


    rating = request.form.get('bookrate')
    Review = request.form.get('bookreview')
    anon = request.form.get('isanon')
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    now = datetime.strptime(now, '%Y-%m-%d %H:%M')
    israte=True
    isreview=True
    
    isanon = False
    if anon == 'on':
        isanon = True
    if not rating:
        israte=False
    if not Review:
        isreview=False
    

    Reviews = review(user_id=session['user_id'], book_id=books.id, ratings=rating, review=Review, is_rated=israte, is_reviewed=isreview, is_anonymous=isanon, reviews_count=count, date_created=now)
    db.session.add(Reviews)
    db.session.commit()

    return redirect(url_for('mybooks'))
 
        # My Reviews Routes

@app.route('/mybooks/myreviews')
@auth_Required
def myreviews():
    reviews = review.query.filter_by(user_id=session['user_id']).all()
    books = book.query.all()
    sections = Section.query.all()
    count = review.query.filter_by(user_id=session['user_id'],is_rated=True).count()

    return render_template('review/myreviews.html',reviews=reviews, books=books, sections=sections, user=current_user(),count=count)


@app.route('/mybooks/myreviews/<int:review_id>/delete', methods=['POST'])
@auth_Required
def delete_review_post(review_id):
    Review = review.query.get(review_id)
    if not Review:
        flash('Review does not exist')
        return redirect(url_for('myreviews'))
    
    db.session.delete(Review)
    db.session.commit()

    flash('Book Review deleted successfully')
    return redirect(url_for('myreviews'))


@app.route('/mybooks/myreviews/<int:review_id>/edit')
@auth_Required
def edit_review(review_id):
    Review = review.query.get(review_id)
    if not Review:
        flash('Review does not exist')
        return redirect(url_for('myreviews'))
    books = book.query.get(Review.book_id)
    sections = Section.query.get(books.section_id)
    
    return render_template('review/editreview.html',reviews=Review, books=books, sections=sections, user=current_user())

@app.route('/mybooks/myreviews/<int:review_id>/edit', methods=['POST'])
@auth_Required
def edit_review_post(review_id):
    Review = review.query.get(review_id)
    if not Review:
        flash('Review does not exist')
        return redirect(url_for('myreviews'))

    rating = request.form.get('bookrate')
    Reviews = request.form.get('bookreview')
    anon = request.form.get('isanon')
    is_edited = True
    is_rated = True
    is_reviewed = False
    if Reviews:
        is_reviewed = True
    is_anonymous = False
    if anon == 'on':
        is_anonymous = True

    Review.ratings = rating
    Review.review = Reviews
    Review.is_rated = is_rated
    Review.is_reviewed = is_reviewed
    Review.is_anonymous = is_anonymous
    Review.is_edited = is_edited
    db.session.commit()
    
    flash('Review Edited Successfully')
    return redirect(url_for('myreviews'))


@app.route('/mybooks/myreviews/<int:review_id>/view')
@auth_Required
def view_review(review_id):
    Review = review.query.get(review_id)
    if not Review:
        flash('Review does not exist')
        return redirect(url_for('myreviews'))
    books = book.query.get(Review.book_id)
    sections = Section.query.get(books.section_id)

    return render_template('review/viewreview.html',reviews=Review, books=books, sections=sections, user=current_user())


    # Download PDFS of Books

@app.route('/mybooks/<int:id>/download', methods=['POST'])
@auth_Required
def download(id):
    transactions = Transaction.query.filter_by(user_id=session['user_id']).order_by(Transaction.datetime.desc()).all()
    sections = Section.query.all()
    books=book.query.get(id)
    if not transactions:
        flash('No Books to Download')
        return redirect(url_for('mybooks'))
    if not books:
        flash('Book does not exist Anymore. Kindly Contact Admin at admin@librarystories.com')
        return redirect(url_for('mybooks'))
    if not books.book_link:
        buffer = BytesIO()
        c = canvas.Canvas(buffer,pagesize=letter)
        width,height = letter
        c.drawString(250, 750, books.title)
        c.drawString(250, 720, "By "+books.author)
        if books.publisher:
            c.drawString(250, 690, "From "+books.publisher)
        text=books.content
        words=textwrap.wrap(text, width=100)
        y=600
        for word in words:
            if y<50:
                c.showPage()
                y=height-50
            c.drawString(50,y,word)
            y -= 15
        c.save()
        buffer.seek(0)
        name = books.title+'.pdf'
        flash('E-Book Downloaded Successfully')
        return send_file(buffer, as_attachment=True, download_name=name) 
        
    else:
        return redirect(books.book_link)
       

# Wishlist Routes
    
@app.route('/wishlist/<int:book_id>/add',methods=['POST'])
@auth_Required
def add_to_wishlist(book_id):
    books=book.query.get(book_id)
    sections = Section.query.get(books.section_id)
    if not books:
        flash('Book does not exist')
        return redirect(url_for('index'))
    if not sections:
        flash('Book Section does not exist')
        return redirect(url_for('index'))
    
    if Wishlist.query.filter_by(user_id=session['user_id'], book_id=book_id).first():
        flash('Book already in Wishlist')
        return redirect(url_for('index'))
    
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    now = datetime.strptime(now, '%Y-%m-%d %H:%M')

    wishlist = Wishlist(user_id=session['user_id'], book_id=book_id, date_added=now, is_wished=True)
    db.session.add(wishlist)
    db.session.commit()

    flash('Book Added to your Wishlist Successfully')
    return redirect(url_for('view_book',id=books.id))

@app.route('/mybooks/mywishlist')
@auth_Required
def mywishlist():
    wishlists = Wishlist.query.filter_by(user_id=session['user_id']).all()
    books = book.query.all()
    sections = Section.query.all()
    
    return render_template('user/wishlist.html',wishlists=wishlists, books=books, sections=sections, user=current_user())

@app.route('/mybooks/mywishlist/<int:wishlist_id>/delete', methods=['POST'])
@auth_Required
def delete_wishlist(wishlist_id):
    Wishlists = Wishlist.query.get(wishlist_id)
    if not Wishlists:
        flash('Wishlist does not exist')
        return redirect(url_for('mywishlist'))
    
    db.session.delete(Wishlists)
    db.session.commit()
    flash('Wishlisted Book Removed successfully')
    return redirect(url_for('mywishlist'))

# Favorites Routes

@app.route('/favorite/<int:book_id>/add',methods=['POST'])
@auth_Required
def add_to_favorites(book_id):
    books=book.query.get(book_id)
    sections = Section.query.get(books.section_id)
    if not books:
        flash('Book does not exist')
        return redirect(url_for('index'))
    if not sections:
        flash('Book Section does not exist')
        return redirect(url_for('index'))
    
    if Favorite.query.filter_by(user_id=session['user_id'], book_id=book_id).first():
        flash('Book already in Favorites')
        return redirect(url_for('index'))

    favorite = Favorite(user_id=session['user_id'], book_id=book_id, is_favourite=True)
    db.session.add(favorite)
    db.session.commit()

    flash('Book Added to your Favorites Successfully')
    return redirect(url_for('view_book',id=books.id))

@app.route('/mybooks/myfavorites')
@auth_Required
def myfavorite():
    favorites = Favorite.query.filter_by(user_id=session['user_id']).all()
    books = book.query.all()
    sections = Section.query.all()
    
    return render_template('user/favorite.html', favorites=favorites, books=books, sections=sections, user=current_user())

@app.route('/mybooks/myfavorites/<int:favorite_id>/delete', methods=['POST'])
@auth_Required
def delete_favorite(favorite_id):
    favorites = Favorite.query.get(favorite_id)
    if not favorites:
        flash('Favorite does not exist')
        return redirect(url_for('myfavorite'))
    
    db.session.delete(favorites)
    db.session.commit()
    flash('Favorite Book Removed successfully')
    return redirect(url_for('myfavorite'))



# User Stats

@app.route('/mybooks/stats')
@auth_Required
def user_stats():
    sections = Section.query.all()
    books = book.query.all()
    borrowed_books = [[BookAccess.query.filter_by(book_id=Book.id, user_id=current_user().id).count(),Book.title] for Book in books]
    top_books = sorted(borrowed_books, key=lambda x: x[0], reverse=True)
    
    section_borrow_counts = {(section.name, section.id): 0 for section in sections}
    for Book in books:
        borrowed_count = BookAccess.query.filter_by(book_id=Book.id, user_id=current_user().id).count()
        for i in section_borrow_counts:
            if Book.section_id in i:
                    section_borrow_counts[i] += borrowed_count
    sorted_sections = sorted(section_borrow_counts.items(), key=lambda x: x[1], reverse=True)
    
    if top_books:
        top_books = top_books[:5]
        books = [book[1] for book in top_books]
        counts = [book[0] for book in top_books]
        colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'orange']
        plt.bar(books, counts, edgecolor='black', color=colors)
        plt.xlabel('Book Titles')
        plt.ylabel('# of Times Book Borrowed')
        plt.title('Top 5 Borrowed Books')
        plt.tick_params(axis='x', which='major', labelsize=5)
        plt.savefig('static/charts/users/topbooks.png', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close()

    if sorted_sections:
        sections = [section[0][0] for section in sorted_sections]
        counts = [section[1] for section in sorted_sections]
        print(counts)
        colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'orange','blue','pink','purple','silver','orange']
        plt.bar(sections, counts, edgecolor='black', color=colors)
        plt.xlabel('Section Names')
        plt.ylabel('# of Times Books Borrowed')
        plt.title('Top Sections')
        plt.tick_params(axis='x', which='major', labelsize=5)

        plt.savefig('static/charts/users/topsections.png', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close()

    return render_template('stats/userstats.html', user=current_user())
# Admin Stats

@app.route('/admin/stats')
@admin_required
def admin_stats():
    sections = Section.query.all()
    sections_names = [section.name for section in sections]
    sections_counts = [book.query.filter_by(section_id=section.id).count() for section in sections]
    user_counts = [User.query.filter_by(is_author=True).count(),User.query.filter_by(role="User").count()]
    books = book.query.all()
    borrowed_books = [[BookAccess.query.filter_by(isgranted=True,book_id=Book.id).count(),Book.title] for Book in books]
    top_books = sorted(borrowed_books, key=lambda x: x[0], reverse=True)
    

    section_borrow_counts = {(section.name, section.id): 0 for section in sections}
    for Book in books:
        borrowed_count = BookAccess.query.filter_by(isgranted=True, book_id=Book.id).count()
        for i in section_borrow_counts:
            if Book.section_id in i:
                    section_borrow_counts[i] += borrowed_count
    sorted_sections = sorted(section_borrow_counts.items(), key=lambda x: x[1], reverse=True)


    if sections:
        colors = ['blue','pink','purple','silver','orange','cyan', 'lightblue', 'lightgreen', 'tan', 'olivedrab', 'rosybrown', 'gray', 'saddlebrown']
        plt.bar(sections_names, sections_counts, edgecolor='black', color=colors)
        plt.xlabel('Section Names')
        plt.ylabel('# of Books')
        plt.title('# of Books in each Section')
        plt.tick_params(axis='x', which='major', labelsize=5)

        plt.savefig('static/charts/admin/noofbooks.png', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close()

    if user_counts:
        total = sum(user_counts)
        colors = ['cyan', 'lightblue']
        wedgeprops = {'linewidth': 1, 'edgecolor': 'black'}
        plt.pie(user_counts, labels=["Authors","Users"], colors=colors,  startangle=90, explode=(0, 0.1) , wedgeprops=wedgeprops, autopct=lambda x: f'{x:.1f}%\n({int(round(x * total / 100.0)):,d})')
        plt.title('# of Authors and Users')
        

        plt.savefig('static/charts/admin/noofusers.png', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close()

    if top_books:
        top_books = top_books[:5]
        books = [book[1] for book in top_books]
        counts = [book[0] for book in top_books]
        colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'orange']
        plt.bar(books, counts, edgecolor='black', color=colors)
        plt.xlabel('Book Titles')
        plt.ylabel('# of Times Book Borrowed')
        plt.title('Top 5 Borrowed Books')
        plt.tick_params(axis='x', which='major', labelsize=5)

        plt.savefig('static/charts/admin/topbooks.png', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close()
    
    if sorted_sections:
        sections = [section[0][0] for section in sorted_sections]
        counts = [section[1] for section in sorted_sections]
        colors = ['cyan', 'lightblue', 'lightgreen', 'tan', 'orange','blue','pink','purple','silver','orange']
        plt.bar(sections, counts, edgecolor='black', color=colors)
        plt.xlabel('Section Names')
        plt.ylabel('# of Times Books Borrowed')
        plt.title('Top Sections')
        plt.tick_params(axis='x', which='major', labelsize=5)

        plt.savefig('static/charts/admin/topsections.png', dpi=300, bbox_inches='tight')
        plt.clf()
        plt.close()
    

    return render_template('stats/stats.html', user=current_user())


# Author Routes

@app.route('/profile/become_author')
@auth_Required
def become_author():
    user=current_user()
    if user.is_author:
        flash('You are already an Author')
        return redirect(url_for('index'))
    
    return render_template('author/become_author.html', user=current_user())


@app.route('/profile/become_author', methods=['POST'])
@auth_Required
def become_author_post():
    user = current_user()
    if user.is_author:
        flash('You are already an Author')
        return redirect(url_for('index'))
    datec = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"),"%Y-%m-%d %H:%M")
    user.date_upgraded = datec
    user.is_author = True
    user.role = "AUTHOR"
    db.session.commit()
    
    flash('Congratulations!! Successfully You are now an Author at Library-Stories ')
    return redirect(url_for('author'))


@app.route('/author')
@author_required
def author():
    books = book.query.filter_by(author=current_user().username).all()
    sections = Section.query.all()
    author_books = author_book.query.filter_by(user_id=current_user().id).all()
    count = author_book.query.filter_by(user_id=current_user().id).count()
    counts = book.query.filter_by(author=current_user().username).count()
    return render_template('author/author.html', books=books,author_books=author_books, sections=sections, user=current_user(), count=count, counts=counts)

@app.route('/author/suggest')
@author_required
def suggest():
    user=current_user()
    if not user.is_author:
        flash('You are not an Author and donot have required permissions')
        return redirect(url_for('index'))
    
    return render_template('author/author_add.html', user=current_user())

@app.route('/author/suggest', methods=['POST'])
@author_required
def suggest_post():
    title = request.form.get('name')
    pub = request.form.get('publisher')
    desc = request.form.get('desc')
    ssec = request.form.get('ssec')
    pages = request.form.get('pages')
    volume = request.form.get('volume')
    price = request.form.get('price')
    bkimg = request.form.get('bookimg')
    section = request.form.get('section')
    content = request.form.get('content')
    isaudible = request.form.get('isaudi')
    link = request.form.get('link')
    
    if not title or not price or not section:
        flash('Please Fill out all Required Fields')
        return redirect(url_for('suggest'))
    try:
        price = float(price)
    
    except ValueError:
        flash('Invalid Book Price Please set Correct One')
        return redirect(url_for('suggest'))

    if price < 0:
        flash('Invalid Book Price')
        return redirect(url_for('suggest'))
    
    if not desc:
        desc = "No Description Available"
    if not ssec:
        ssec = "No Sub-sections Available"
    if not pages:
        pages = 1
    if not volume:
        volume = 1
    if not pub:
        pub = "No Book Publisher Available"
    if isaudible == 'on':
        if not content:
            flash("IF Book is Audible Then Content Cannot be Empty")
            return redirect(url_for('suggest'))
        isaudible = True
    else:
        isaudible = False

    author_books = author_book.query.filter_by(user_id=current_user().id).all()
    count = author_book.query.filter_by(user_id=current_user().id).count()
    if count > 25:
        flash('You have reached the maximum limit to Suggest Books')
        return redirect(url_for('author'))
    
    temp_book = author_book(user_id=current_user().id, title=title, price=price, sections=section, desc=desc, publisher=pub, subsections=ssec, pages=pages, volumne=volume, book_image=bkimg, content=content, is_audible=isaudible, book_link=link, is_suggested=True)
    db.session.add(temp_book)
    db.session.commit()

    flash('Book Suggested to Admin Successfully')
    return redirect(url_for('author'))


@app.route('/author/<int:suggest_id>/delete')
@author_required
def delete_suggest(suggest_id):
    suggest = author_book.query.get(suggest_id)
    if not suggest:
        flash('Suggested Book does not exist')
        return redirect(url_for('author'))
    return render_template('author/author_delete.html', suggest=suggest, user=current_user())


@app.route('/author/<int:suggest_id>/delete', methods=['POST'])
@author_required
def delete_suggest_post(suggest_id):
    suggest = author_book.query.get(suggest_id)
    if not suggest:
        flash('Suggested Book does not exist')
        return redirect(url_for('author'))
    
    db.session.delete(suggest)
    db.session.commit()
    flash('Book Suggestion Withdrawn Successfully')
    return redirect(url_for('author'))


@app.route('/author/<int:suggest_id>/show')
@author_required
def author_show(suggest_id):
    Book=author_book.query.get(suggest_id)
    section_name = Book.sections
    users = User.query.all()
    avg=0
    
    if not Book:
        flash('Suggested Book does not exist')
        return redirect(url_for('author'))

    return render_template('author/author_show.html',users=users, section_name=section_name, book=Book, user=current_user(), overall=avg)

 # Admin Author Routes

@app.route('/admin/author')
@admin_required
def admin_author():
    author_books = author_book.query.all()
    users = User.query.all()
    sections = Section.query.all()
    count = author_book.query.filter_by(is_suggested=True).count()

    return render_template('admin/author_approval.html', author_books=author_books, users=users, sections=sections, user=current_user(),count=count)


@app.route('/admin/author/<int:suggest_id>/show')
@admin_required
def admin_author_show(suggest_id):
    Book=author_book.query.get(suggest_id)
    section_name = Book.sections
    users = User.query.all()
    avg=0
    
    if not Book:
        flash('Suggested Book does not exist')
        return redirect(url_for('author'))

    return render_template('author/author_show.html',users=users, section_name=section_name, book=Book, user=current_user(), overall=avg)

@app.route('/admin/author/<int:suggest_id>/reject', methods=['POST'])
@admin_required
def admin_author_reject(suggest_id):
    suggest = author_book.query.get(suggest_id)
    if not suggest:
        flash('Suggested Book does not exist')
        return redirect(url_for('admin_author'))
    
    db.session.delete(suggest)
    db.session.commit()
    flash('Book Suggestion Rejected Successfully')
    return redirect(url_for('admin_author'))

@app.route('/admin/author/<int:suggest_id>/approve', methods=['POST'])
@admin_required
def admin_author_approve(suggest_id):
    suggest = author_book.query.get(suggest_id)
    if not suggest:
        flash('Suggested Book does not exist')
        return redirect(url_for('admin_author'))
    users = User.query.all()
    sections = Section.query.all()
    sec_found = False
    for section in sections:
        if (section.name).lower() == (suggest.sections).lower():
            section_id = section.id
            sec_found = True
    if not sec_found:
        name = (suggest.sections).capitalize()
        desc = "This is a Section for "+name+" Genre"
        daten = datetime.now().strftime("%Y-%m-%d %H:%M")
        datec = datetime.strptime(daten,"%Y-%m-%d %H:%M")
        section = Section(name=name, desc=desc, date_created=datec)
        db.session.add(section)
        db.session.commit()
        sections = Section.query.all()

        for section in sections:
            if (section.name).lower() == (suggest.sections).lower():
                section_id = section.id


    for user in users:
        if user.id == suggest.user_id:
            author = user.username
    
    adddate = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")

    Book = book(title=suggest.title, author=author, price=suggest.price, section_id=section_id, subsections=suggest.subsections, desc=suggest.desc, publisher=suggest.publisher, pages=suggest.pages, volumne=suggest.volumne, book_image=suggest.book_image, content=suggest.content, is_audible=suggest.is_audible, book_link=suggest.book_link, is_upcoming=False, date_added=adddate)
    db.session.add(Book)
    db.session.delete(suggest)
    db.session.commit()

    flash('Book Suggestion Approved Successfully and Book Added to Respective Section')
    return redirect(url_for('admin_author'))

  # Blacklist Functionality

@app.route('/admin/userlist')
@admin_required
def user_list():
    userss = User.query.all()
    Blacklist = blacklist.query.filter_by(is_blacklisted=True).all()
    blacklisted_users = []
    for black in Blacklist:
        for user in userss:
            if user.id == black.user_id:
                blacklisted_users.append((user,black))
    Bookaccess = BookAccess.query.all()
    booksaccess = []
    for user in userss:
        user.books_requested = 0
        for access in Bookaccess:
            if access.user_id == user.id and user not in blacklisted_users:
                user.books_requested += 1
        booksaccess.append((user, user.books_requested))
    for i in Blacklist:
        for j in userss:
            if i.user_id == j.id:
                booksaccess.remove((j,j.books_requested))
                userss.remove(j)
    return render_template('admin/blacklist.html', users=userss, user=current_user(), Blacklist=blacklisted_users, Bookaccess=booksaccess)

@app.route('/admin/userlist/<int:user_id>/blacklist')
@admin_required
def blacklist_user(user_id):
    users = User.query.get(user_id)
    if not users:
        flash('User does not exist Anymore')
        return redirect(url_for('user_list'))
    return render_template('admin/blacklistform.html', users=users, user=current_user())

@app.route('/admin/userlist/<int:user_id>/blacklist', methods=['POST'])
@admin_required
def blacklist_user_post(user_id):
    users = User.query.get(user_id)
    if not users:
        flash('User does not exist Anymore')
        return redirect(url_for('user_list'))
    reason = request.form.get('reason')
    till = request.form.get('till')
    if not reason:
        flash('Please Provide a Reason for Blacklisting User')
        return redirect(url_for('blacklist_user', user_id=user_id))
    
    now = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"), '%Y-%m-%d %H:%M')
    due = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"), '%Y-%m-%d %H:%M') + timedelta(int(till))
    isblack = True
    black = blacklist(user_id=user_id, reason=reason, is_blacklisted=isblack, blacklisted_at=now, blacklisted_till=due)
    db.session.add(black)
    db.session.commit()
    flash('User Blacklisted Successfully')
    return redirect(url_for('user_list'))

@app.route('/admin/userlist/<int:user_id>/unblacklist', methods=['POST'])
@admin_required
def unblacklist_user(user_id):
    black = blacklist.query.filter_by(user_id=user_id, is_blacklisted=True).first()
    if not black:
        flash('User is not Blacklisted')
        return redirect(url_for('user_list'))
    db.session.delete(black)
    db.session.commit()
    flash('User\'s Account removed from blacklist Successfully')
    return redirect(url_for('user_list'))

@app.route('/admin/userlist/<int:user_id>/delete_user')
@admin_required
def delete_user(user_id):
    users = User.query.get(user_id)
    if not users:
        flash('User does not exist Anymore')
        return redirect(url_for('user_list'))
    return render_template('admin/deleteuser.html', users=users, user=current_user())

@app.route('/admin/userlist/<int:user_id>/delete_user', methods=['POST'])
@admin_required
def delete_user_post(user_id):
    users = User.query.get(user_id)
    if not users:
        flash('User does not exist Anymore')
        return redirect(url_for('user_list'))
    password = request.form.get('pass')
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, password):
        flash('Incorrect Password! Account Deletion Failed')
        return redirect(url_for('user_list'))
    
    db.session.delete(users)
    db.session.commit()
    flash('User\'s Account Deleted Successfully')
    return redirect(url_for('user_list'))








  #### FINISHED ####