from flask import FLASK,  render_template, request, jsonify, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from  flask_migrate import Migrate
from  flask_login import LoginManager, UserMixin, current_user, login_user, login_required
from sqlalchemy import or_, Table
from sqlalchemy.exc import SQLAlchemyError
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

class BookDatabaseException(Exception):
      pass
  
app =Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'login'

favorites = db.Table('favorites',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
     db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True)
)

db.init_app(app)
migrate.init_app(app,db)
login_manager.init_app(app)


class User(UserMixin, db.Model):
    id = db. Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable= False)
    password_hash = db.Column(db.String(12IOP8))
    wishlists = db.relationship('Wishlist', backref='user', lazy='dynamic')
    favorite_books = db.relationship('Book', secondary='favorite', back_populates='favorited_by')

    def set_password(self, password):
       self.password_hash = generate_password_hash(password)

    def check_password(self,password):
       return check_password_hash(self.password_hash,password)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author= db.Column(db.Colum(100), nullable= False)
    publication_year = db.Column(db.Integer)
    isbn =db.Column(db.String(13))
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(13))
    reviews = db.relationship('Review', backref='book', lazy=True)
    wishlists = db.relationship('Wishlist', backref='book', lazy='dynamic')
    
class Review(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db. Text)
    create_at = db.Column(db.DateTime, dafault=datetime.utcnow)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable= False)
    user = db.relationship('User', backref=db.backref('review', lazy=True))

class Wishlist(db.Model):
    id =db.Column(db.Integer, primary_key=False)
    rating = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'),nullable=False)
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
    
    @app.route('/book/<int:id>')  
    def book_detail(id):
        book = Book.query.get_or_404(id)
        is_favorite = False
        if current_user.is_authenticated:
            is_favorite = Wishlist.query.filter_by(user_id=current_user.id,book_id=id).first() is not None
        return jsonify({
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'publication_year': book.publication_year,
            'isbn': book.isbn,
            'description':book.cover_url,
            'is_favorite': is_favorite,
            'reviews': [{
                'id': review.id,
                'rating': review.rating,
                'comment': review.comment,
                'created_at': review.created_at.isoformat(),
                
                'user_id': review.user_id
                
            } for reveiw in reviews]
            
        })
    @app.route('/add_edit_book', methods=['GET', 'POST'])
    @login_required
    def add_edit_book(book_id=None):
      app.logger.info(f"Entering add_edit_book function with book_id:{book_id}")
      book = Book.query.get(book_id) if book_id else None
      if request.method == 'POST':
            try:
                title = request.form.get('title')
                author = request.form.get('author')
                publication_year = request.form.get('publication_year')
                isbn = request.form.get('isbn')
                description =request.form.get('cover_url')
                cover_url = request.form.get('cover_url')
                
                app.logger.debug(f"Received form data: title={title}, author={author}, publication_year={publication_year}, isbn=[isbn]")
                
                if not title or not author:
                    app.logger.warning("Title or author is missing")
                    flash('Title and author are requrired fields.','error')
                    return render_template('add_edit_book.html', book=book)
                
                if book:
                    app.logger.info(f"Updating existing booking with id:{book.id} ")
                    book.title = title
                    book.author = author
                    book.publication_year = publication_year
                    book.isbn =isbn
                    book.description = description
                    book.cover_url = cover_url
                    message ='Book updated successfully!'
                else:
                    app.logger.info("Adding new book")
                    book = Book(
                        title= title,
                        author=author,
                        publication_year=publication_year,
                        isbn=isbn,
                        description= description,
                        cover_url=cover_url
                    )
                    db.session.add(book)
                    message = 'Book add successfully!'
                    
                db.session.commit() 
                app.logger.info(f"Book {'updated' if book_id else 'added'} successfully with id: {book.id}")
                flash(message, 'success')
                return redirect(url_for('book_detail', id=book.id))
            except BookDatabaseException as e:
              db.session.rollback()
              app.logger.error(f"Error{'updating' if book else 'adding'} book:{str(e)}")
              flash(str(e),  'error')
              return render_template('add_edit_html', book=book), 400
            except SQLAlchemyError as e:
                db.session.rollback()
                app.logger.error(f"Database error {'updating' if book else 'adding'}  book: {str(e)}")
                flash('A database error occured. Please try again later.', 'error')
                return render_template('add_edit_book.html', book=book),500
            
                return render_template('add_edit_book.html', book=book) 
         
    @app.route('/search')  
    def search():
        query = request.args.get('q','')
        books= Book.query.filter(
            or_(
                Book.title.ilike(f'%{query}%'),
                Book.author.ilike(f'%{query}%')
                
            )
        ).all()
        return jsonify([{
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'publication_year': book.publication_year,
            'isbn': book.isbn,
            'description': book.description,
            'cover_url': book.cover_url
            
        } for book in books])
        
        
    @app.route('/book/<int:book_id>/review', methods=['POST'])
    @login_required
    def add_review(book_id):
        app.logger.info(f"Adding review for book_id:{book_id}")
        try:
            rating = request.form.get('rating')
            comment = request.form.get('comment', '').strip()
            app.logger.debug(f"Received rating:{rating}, comment: {comment} ")
            
            if not rating or not rating.isdigit() or int(rating) < 1 or int(rating) > 5:
               app.logger.warning(f"Invalid rating:{rating}")
               flash('Please provide a valid rating between 1 and 5.', 'error')
               return redirect(url_for('book_details', id=book_id))
            if not comment:
                app.logger.warning("Empty comment received")
                flash('Please provide a comment for your review.', 'error')
                return redirect(url_for('book_details', id=book_id))
        
            new_review = Review(
                rating=int(rating),
                comment=comment,
                book_id = book_id,
                user_id = current_user.id
            )
            db.session.add(new_review)
            db.session.commit()
            app.logger.info(f"Review added successfully for book_id: {book_id}")
            flash(f'Review added successfully! Rating: {rating}', 'success')
            return redirect(url_for('book_details_id'))
        except BookDatabaseException as e:
            db.session.rollback()
            app.logger.error(f"Error adding review for book_id {book_id}: {str(e)}")
            flash(str(e), 'error')
            return redirect(url_for('book_datails', id=book_id))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Unexpected error adding review for book_id {book_id}: {str(e)}")
            flash('An unexpected error occurred while adding the review. Please try again later.', 'error')
            
            return redirect(url_for('book_details', id=book_id))
        
@app.route('/api/user/<int:user_id>/wishlist', methods=['POST'])
@login_required
def add_to_wishlist(user_id):
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403

    book_id = request.json.get('book_id')
    if not book_id:
        return jsonify({"error": "Book ID is required"}), 400

    existing_wishlist = Wishlist.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_wishlist:
        return jsonify({"message": "Book already in wishlist"}), 200

    new_wishlist = Wishlist(user_id=user_id, book_id=book_id)
    db.session.add(new_wishlist)
    db.session.commit()
    
    return jsonify({"message": "Book added to wishlist successfully"}), 201

        

@app.route('/api/user/<int:book_id>/wishlist/<int:book_id>', methods=['DELETE'])
@login_required
def remove_from_wishlist(user_id, book_id):
    if current_user.id != user_id:
        return jsonify({"error": "Unauthorized"}), 403
    wishlist_item = Wishlist.query.filter_by(user_id, book_id=book_id).first()
    if not wishlist_item:
        return jsonify({"error": "Book not found in whishlist"}), 404
    db.session.deleted(wishlist_item)
    db.session.commit()
    return jsonify({"message": "Book remove from wishlist successfully"}), 200

@app.route('/register', methods=['GET' 'POST'])
def register():
     if current_user.is_authenticated:
         return redirect(url_for('home'))
     if request.method =='POST':
         username = request.form.get('username')
         email =request.form.get('email')
         password =request.form.get('password')
         if User.query.filter_by(username=username).first():
             flash('Username already registered.', 'error')
         elif User.query.filter_by(email=email).first():
             flash('Email already registered.', 'error')
         else:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
     return render_template('register'.html)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method=='POST':
         username= request.form.get('username')
         password=request.form.get('password')
         user= User.query.filter_by(username=username).first()
         if user and user.check_password(password):
             login_user(user)
             flash('Logged in successfully.', 'success')
             return redirect(url_for('home'))
         else:
             flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/delete_book/<int:id>', methods=['POST'])
@login_required
def delete_book(id):
    book= Book.query.get_or_404(id)
    try:
        db.session.delete(book)
        db.session.commit()
        flash('Book successfully deleted.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f"Error deleting book:{str(e)}")
        flash('An error occurred while deleting the book.please try again.', 'error')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Unexpected error deleting book:{str(e)}")
        flash('An unexpected error occurred.please.contact  support.', 'error')
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    
     
        
        
            
          
            
        
            
                   
                    
                
          
     
    
    

