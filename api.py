from flask_restful import Resource, Api ,reqparse, abort
from app import app
from models import db, Section, book
from datetime import datetime
#from flask import jsonify, session
import json

api = Api(app)



 # CRUD operations for Section


section_parser = reqparse.RequestParser()
section_parser.add_argument('name', type=str, required=True, help='Name is required')
section_parser.add_argument('desc', type=str, required=False)


class SectionListResource(Resource):
    def get(self):
        sections = Section.query.all()
        return [
            {'id': section.id, 
             'name': section.name, 
             'desc': section.desc}
               for section in sections ]

    def post(self):
        args = section_parser.parse_args()
        
        daten = datetime.now().strftime("%Y-%m-%d %H:%M")
        datec = datetime.strptime(daten,"%Y-%m-%d %H:%M")

        section = Section(name=args['name'], desc=args['desc'], date_created=datec)
        db.session.add(section)
        db.session.commit()
        return {'message': 'Section created successfully', 'id': section.id}, 201


# Resource for a specific section
class SectionResource(Resource):
    def get(self, section_id):
        section = Section.query.get_or_404(section_id)
        return {'id': section.id, 
                'name': section.name, 
                'desc': section.desc, 
                'date_created': section.date_created.strftime("%Y-%m-%d %H:%M")
                }

    def put(self, section_id):
        section = Section.query.get_or_404(section_id)
        args = section_parser.parse_args()
        section.name = args['name']
        section.desc = args['desc']
        db.session.commit()
        return {'message': 'Section updated successfully'}

    def delete(self, section_id):
        section = Section.query.get_or_404(section_id)
        db.session.delete(section)
        db.session.commit()
        return {'message': 'Section deleted successfully'}


api.add_resource(SectionListResource, '/api/sections')
api.add_resource(SectionResource, '/api/sections/<int:section_id>')


   # CRUD operations for book

book_parser = reqparse.RequestParser()
book_parser.add_argument('title', type=str, required=True, help='Title is required')
book_parser.add_argument('author', type=str, required=True, help='Author is required')
book_parser.add_argument('subsections', type=str, required=False)
book_parser.add_argument('publisher', type=str, required=False)
book_parser.add_argument('pages', type=int, required=False)
book_parser.add_argument('volumne', type=int, required=False)
book_parser.add_argument('desc', type=str, required=False)
book_parser.add_argument('price', type=float, required=False)
book_parser.add_argument('book_image', type=str, required=False)
book_parser.add_argument('content', type=str, required=False)
book_parser.add_argument('book_link', type=str, required=False)

class BooksListResource(Resource):
    def get(self):
        books = book.query.all()
        return [{'id': Book.id, 
                 'title': Book.title, 
                 'author': Book.author,
                 'section_id':Book.section_id,
                 'Description':Book.desc,
                 'Publisher':Book.publisher,
                 'pages':Book.pages,
                 'volume':Book.volumne,
                 'price':Book.price,
                 'book_image':Book.book_image,
                 'content':Book.content,
                 'book_link':Book.book_link,
                 'subsections':Book.subsections,
                 'is_audible':Book.is_audible
                 } for Book in books]

class BookListResource(Resource):
    def get(self, section_id):
        books = book.query.filter_by(section_id=section_id).all()
        return [{'id': Book.id, 
                 'title': Book.title, 
                 'author': Book.author,
                 'section_id':Book.section_id,
                 'Description':Book.desc,
                 'Publisher':Book.publisher,
                 'pages':Book.pages,
                 'volume':Book.volumne,
                 'price':Book.price,
                 'book_image':Book.book_image,
                 'content':Book.content,
                 'book_link':Book.book_link,
                 'subsections':Book.subsections,
                 'is_audible':Book.is_audible
                 } for Book in books]


    def post(self,section_id):
        args = book_parser.parse_args()
        adddate = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")
        Book = book(title=args['title'], author=args['author'], section_id = section_id, subsections=args['subsections'], publisher=args['publisher'], pages=args['pages'], volumne=args['volumne'], desc=args['desc'], price=args['price'], book_image=args['book_image'], content=args['content'], book_link=args['book_link'], date_added=adddate)
        db.session.add(Book)
        db.session.commit()
        return {'message': 'Book created successfully', 'id': Book.id}, 201

# Resource for a specific book

class BookResource(Resource):
    def get(self,section_id, book_id):
        Book = book.query.get_or_404(book_id)
        return {'id': Book.id, 
                'title': Book.title, 
                'author': Book.author,
                'section_id':Book.section_id,
                'Date Added': json.dumps(Book.date_added, default=str),

                'Description':Book.desc,
                'Publisher':Book.publisher,
                'pages':Book.pages,
                'volume':Book.volumne,
                'price':Book.price,
                'book_image':Book.book_image,
                'content':Book.content,
                'book_link':Book.book_link,
                'subsections':Book.subsections,
                'is_audible':Book.is_audible}

    def put(self,section_id, book_id):
        Book = book.query.get_or_404(book_id)
        args = book_parser.parse_args()
        Book.title = args['title']
        Book.author = args['author']
        Book.subsections = args['subsections']
        Book.publisher = args['publisher']
        Book.pages = args['pages']
        Book.volumne = args['volumne']
        Book.desc = args['desc']
        Book.price = args['price']
        Book.book_image = args['book_image']
        Book.content = args['content']
        Book.book_link = args['book_link']


        db.session.commit()
        return {'message': 'Book updated successfully'}

    def delete(self,section_id, book_id):
        Book = book.query.get_or_404(book_id)
        db.session.delete(Book)
        db.session.commit()
        return {'message': 'Book deleted successfully'}

# Add resources to the API
    
api.add_resource(BooksListResource, '/api/books')
api.add_resource(BookListResource, '/api/sections/<int:section_id>/books')
api.add_resource(BookResource, '/api/sections/<int:section_id>/books/<int:book_id>')





