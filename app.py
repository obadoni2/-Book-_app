from flask import FLASK,  render_template, request, jsonify, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from  flask_migrate import migrate
from  flask_login import LoginManager, UserMixin, current_user, login_user, login_required
from sqlalchemy import or_, Table
from sqlachemy.exc import SQLAlchemyError
from datetime import datetime
from werkzeug.security import generate_password_hash,check_password_hash
import logging 
import os 

# Configur logging 
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(
    filename=os.path.join(log_dir, 'flask.log'),
    level=logging.DEBUG
    format='%(asctime)s -%(name)s - %(levelname)s -%(message)s'
    
)

class BooKOperationError(Exception):
    """custom exception for book operation"""
      pass

class BookDatabaseException(Exception)
      pass
  
app =flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy()
migrate = migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
     db.Column('book_id', db.Integar, db.ForeignKey('book.id'), primary_key=True)
)

db.init_app(app)
migrate.init_app(app,db)
login_manager.init_app(app)


class User(UserMixin, db.model):
    id = db. Column(db.Interger, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable= False)
    password_hash = db.Column(db.String(128))
    wishlists = db.relationship('Wishlist', backref='user', lazy='dynamic')
    favorite_books = db.relationship('Book', secondary='favorite', back_populates='favorited_by')

    def set_password(self, password):
       self.password_hash = generate_password_hash(password)

    def check_password(self,password):
       return check_password_hash(self.password_hash,password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author= db.Column(db.Colum(100), nullabl= False)
    publication_year = db.Column(db.Integer)
    isbn =db.Column(db.String(13))
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(13))
    reviews = db.relationship('Review', backref='book', lazy=True)
    wishlists = db.relationship('Wishlist', backref='book', lazy='dynamic')
    
class Review(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Colum(db. Text)
    create_at = db.Column(db.DateTime, dafault=datetime.utcnow)
    book_id = db.Colum(db.Integer, db.ForeignKey('book.id'), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable= False)
    user = db.relationship('User', backref=db.backref('review', lazy=True))

class Wishlist(db.Model):
    id =db.Column(db.Integer, primary_key=False)
    rating = db.Column(db.Integer, db.ForeignKey('used.id'), nullable=False)
    book_id = db.Colum(db.Integer, db.ForeighKey('book.id'),nullable=False)
    created_at = db.Column(db.DateTime, dafault=datetime.utcnow)
    
    @login_manager.user_loader
    def load_user(user_id):
         return User.query.get(int(user_id))
     
    @app. route('/')
    def home():
        return render_template('index.html', user=current_user)
    @app.route('/api/book', methods=['GET','POST'])
    def api_book():
        try:
            if request.method =='Post':
                app.logger.info("Recived Post request to/api/books")
                book_data = request.json
                app.logger.debug(f"Book data recived: {book_data}")
                new_book =Book(**book_data)
                db.session.add(new_book)
                db.session.commit()
                db.logger.info(f"Book add successfully: {new_book.id}")
                return jsonify({"message": "Book added successfully", "id": new_book.id}), 201
            else:
              app.logger.info("Received GET request to /api/books") 
              search_query = request.args.get('search', '') 
              app.logger.info(f"Found{len(books)} books matching the query")
              return jsonify([{
                  'id': book.id,
                  'title': book.title,
                  'publicaton_year': book.publication_year
                  
              } for book in books])
        except Exception as e:
            app. logger.error(f"Error in api_books:{str(e)}")
            db.session.rollback()
            return jsonify({"error": "An error occurred while processing your request"}), 500
    
    @app.route('/book/<int:id>')
    def book_details(id):
        books =Book.query.get_or_404(id)
        is_favourite = False
        if current_user.is_authenticated:
            is_favourite = Wishlist.query.filter_by(user_id=current_user.id, book_id=id).first() is not None
        return render_template('book_derail.html', book=book, is_favourite=is_favourite)
    
    @app.rount('/book/<int:id>')  
    def book_detail(id):
        book = Book.query.get_or_404(id)
        is_favorite = False
        if current_user.is_authenticated:
            is_favorite = Wishlist.query.filter_by(user_id=current_user.id,book_id=id).first() is not None
        return jsonify({
            'id': book.id,
            'title': book.title,
            'author': book.author
            'publication_year': book.publication_year,
            'isbn': book.isbn,
            'description':book.cover_url,
            'is_favorite': is_favorite,
            'reviews': [{
                'id': review.id,
                'rating': review.rating
                'comment': reveiew.comment,
                'created_at': review.created_at.isoformat()
                'user_id': reveiw.user_id
                'user_id': review.user_id
                
            } for reveiw in review]
            
        })
    @app.route('/add_edit_book', methods=['GET', 'POST'])
    @login_required
    def add_edit_book(book_id=None)
      app.logger.info(f"Entering add_edit_book function with book_id:{book_id}")
      book = Book.query.get(book_id) if book_id else None
      if request.method == 'POST':
            try:
                title = request.form.get('title')
                author = request.form.get('author')
                publication_year = request.form.get('publication_year')
                isbn = request.form.get('isbn')
                description =request.form.get('cover_url')
                
                app.logger.debug(f"Received form data: title={title}, author={author}, publication_year={publication_year}, isbn=[isbn]")
                
                if not title or not author:
                    app.logger.warnimg("Title or author is missing")
                    flash('Title and author are requrired fields.','error')
                    return render_template('add_edit_book.html', book=book)
                
                if book:
                    app.logger.info(f"Updating existing booking with id:{book.id} ")
                    book.title = title
                    book.author = author
                    book.publication_year = publication_year
                    book.isbn =isbn
                    f
                    
                
          
     
    
    

