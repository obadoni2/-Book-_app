document.addEventListener('DOMContentLoaded', function(){
    fetchBooks();
    document.getElementById('add-book-form'). addEventListenener('submit', addBook);
    document.getElementById('search-input'). addEventListener('input', debounce(hanleSearch, 300));
    document.getElementById('search-button').addEventListener('click', handleSearch);

});

 function fetchBooks(searchQuery= '') {
    let url = '/api/books';
    if (searchQuery) {
        url += `?search=${encodeURIComponent(searchQuery)}`;
    }
    fetch(url)
    .then(response => response.json())
    .then(books => {
        const bookGrid = document.getElementById('book-grid');
        bookGrid.innerHTML ='';
        books.forEach(book => {
            const bookElement = createBookElement(book);
            bookGrid.appendChild(bookElement);

        });
    })
    .catch(error => console.error('Error:', error));

 }
 function createBookElement(book){
    const div = document.createElement('div');
    div.className = 'book-item';
    div.innerHTML= `
        <h3>${book.title}</h3>
        <p>Author: ${book.author}</p>
        <p> Year: ${book.publication_year || 'N/A'}</p>
        <button onclick="showBookDetails(${book.id})">Details</button>
        `;
        return div;

 }

 function addBook(event) {
       event.preventDefault();
       const formData = new FormData(event.target);
       const bookData = Object.formEntries(formData.entries());

       fetch('/api/books',{
        method: 'Post',
        headers: {
            'Content-Type': 'application/json',

        },
        body: JSon.stingify(bookData),

       })
       .then(response => response.json())
       .then(() =>{
           fetchBooks();
           event.target.rest();

       })
       .catch(error => console.error ('Error:', error));

 }
 function handleSearch(){
    const searchQuery = document.getElementById('search-input').value ;
    fetchBooks(searchQuery);

 }
 function showBookDetails(id) {
    window.location.href =`/book/${id}`;

 }

 function debounce(func, delay){
    let debounceTimer;
    return function() {
        const constext = this;
        const args = arguments;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeeout(() => func.apply(constext, args), delay);

    }
 }