import pytest
from app import app, db, User, Book, Review, Wishlist
from flask_login import current_user
from werkzeug.security import generate_password_hash

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

    with app.app_context():
        db.drop_all()

@pytest.fixture
def auth_client(client):
    user = User(username='testuser', email='test@example.com')
    user.set_password('testpassword')
    with app.app_context():
        db.session.add(user)
        db.session.commit()

    client.post('/login', data={'username': 'testuser', 'password': 'testpassword'})
    return client

def test_home_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Book Database' in response.data

def test_add_book(auth_client):
    response = auth_client.post('/add_edit_book', data={
        'title': 'Test Book',
        'author': 'Test Author',
        'publication_year': '2023',
        'isbn': '1234567890123',
        'description': 'A test book description'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Test Book' in response.data

def test_edit_book(auth_client):
    # First, add a book
    response = auth_client.post('/add_edit_book', data={
        'title': 'Original Title',
        'author': 'Original Author',
        'publication_year': '2023',
        'isbn': '1234567890123',
        'description': 'Original description'
    }, follow_redirects=True)
    assert 'Book added successfully!' in response.get_data(as_text=True)

    # Get the book's ID
    with app.app_context():
        book = Book.query.filter_by(title='Original Title').first()

    # Edit the book
    response = auth_client.post(f'/add_edit_book/{book.id}', data={
        'title': 'Updated Title',
        'author': 'Updated Author',
        'publication_year': '2024',
        'isbn': '9876543210987',
        'description': 'Updated description'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Book updated successfully!' in response.get_data(as_text=True)

    # Check if the book details are correctly displayed after editing
    response = auth_client.get(f'/book/{book.id}')
    assert response.status_code == 200
    assert 'Updated Title' in response.get_data(as_text=True)
    assert 'Updated Author' in response.get_data(as_text=True)
    assert '2024' in response.get_data(as_text=True)
    assert '9876543210987' in response.get_data(as_text=True)
    assert 'Updated description' in response.get_data(as_text=True)

    # Check if the book was actually updated in the database
    with app.app_context():
        updated_book = Book.query.get(book.id)
        assert updated_book.title == 'Updated Title'
        assert updated_book.author == 'Updated Author'
        assert updated_book.publication_year == 2024
        assert updated_book.isbn == '9876543210987'
        assert updated_book.description == 'Updated description'

    # Test with invalid data (empty title)
    response = auth_client.post(f'/add_edit_book/{book.id}', data={
        'title': '',
        'author': 'Updated Author',
        'publication_year': '2024',
        'isbn': '9876543210987',
        'description': 'Updated description'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Title and author are required fields.' in response.get_data(as_text=True)

def test_search_books(auth_client):
    # Add some books
    auth_client.post('/add_edit_book', data={'title': 'Python Programming', 'author': 'John Doe'})
    auth_client.post('/add_edit_book', data={'title': 'Flask Web Development', 'author': 'Jane Smith'})

    # Search for books
    response = auth_client.get('/search?q=Python')
    assert response.status_code == 200
    assert b'Python Programming' in response.data
    assert b'Flask Web Development' not in response.data

def test_book_details(auth_client):
    # Add a book
    auth_client.post('/add_edit_book', data={
        'title': 'Detailed Book',
        'author': 'Detailed Author',
        'publication_year': '2023',
        'isbn': '1234567890123',
        'description': 'A detailed book description'
    })

    # Get the book's ID
    with app.app_context():
        book = Book.query.filter_by(title='Detailed Book').first()

    # View book details
    response = auth_client.get(f'/book/{book.id}')
    assert response.status_code == 200
    assert b'Detailed Book' in response.data
    assert b'Detailed Author' in response.data
    assert b'2023' in response.data
    assert b'1234567890123' in response.data
    assert b'A detailed book description' in response.data

def test_add_review(auth_client):
    # Add a book
    auth_client.post('/add_edit_book', data={'title': 'Review Book', 'author': 'Review Author'})

    # Get the book's ID
    with app.app_context():
        book = Book.query.filter_by(title='Review Book').first()

    # Add a review
    response = auth_client.post(f'/book/{book.id}/reviews', data={
        'rating': 4,
        'comment': 'Great book!'
    }, follow_redirects=True)
    assert response.status_code == 200

    # Check for flash message
    assert 'Review added successfully!' in response.get_data(as_text=True)

    # Check if the review is visible on the book details page
    response = auth_client.get(f'/book/{book.id}')
    assert 'Great book!' in response.get_data(as_text=True)

    # Check for rating within an HTML element using a more flexible approach
    response_text = response.get_data(as_text=True)
    assert 'Rating:' in response_text and '4' in response_text and '/5' in response_text

    # Verify the review is saved in the database
    with app.app_context():
        review = Review.query.filter_by(book_id=book.id).first()
        assert review is not None
        assert review.rating == 4
        assert review.comment == 'Great book!'

    # Test adding an invalid review (missing rating)
    response = auth_client.post(f'/book/{book.id}/reviews', data={
        'comment': 'Invalid review'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Please provide a valid rating between 1 and 5.' in response.get_data(as_text=True)

    # Test adding an invalid review (missing comment)
    response = auth_client.post(f'/book/{book.id}/reviews', data={
        'rating': 3
    }, follow_redirects=True)
    assert response.status_code == 200
    assert 'Please provide a comment for your review.' in response.get_data(as_text=True)

def test_add_to_wishlist(auth_client):
    # Add a book
    auth_client.post('/add_edit_book', data={'title': 'Wishlist Book', 'author': 'Wishlist Author'})

    # Get the book's ID and user's ID
    with app.app_context():
        book = Book.query.filter_by(title='Wishlist Book').first()
        user = User.query.filter_by(username='testuser').first()

    # Add book to wishlist
    response = auth_client.post(f'/api/user/{user.id}/wishlist', json={'book_id': book.id})
    assert response.status_code == 201

    # Check if the book is in the user's wishlist
    with app.app_context():
        wishlist = Wishlist.query.filter_by(user_id=user.id, book_id=book.id).first()
        assert wishlist is not None

def test_responsive_design(client):
    # This test is a placeholder and would typically be done with frontend testing tools
    # Here we're just checking if the viewport meta tag is present
    response = client.get('/')
    assert b'<meta name="viewport"' in response.data

def test_user_registration(client):
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'newpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Registration successful' in response.data

def test_user_login_logout(client):
    # Register a user
    client.post('/register', data={
        'username': 'loginuser',
        'email': 'loginuser@example.com',
        'password': 'loginpassword'
    })

    # Login
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'loginpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Logged in successfully' in response.data

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out' in response.data

def test_accessibility(client):
    # This test is a placeholder and would typically be done with accessibility testing tools
    # Here we're just checking if some basic ARIA attributes are present
    response = client.get('/')
    assert b'role="navigation"' in response.data
    assert b'aria-label' in response.data

# Add more tests as needed for other functionalities