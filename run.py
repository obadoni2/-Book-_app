from app import app

if __name__ == "__main__":
    print("Running on http://127.0.0.1:5000/")
    app.run(debug=True, host="127.0.0.1", port=5000)