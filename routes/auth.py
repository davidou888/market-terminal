from app import app  # Import the Flask app instance from app.py
from flask import request, jsonify  # Import request and jsonify for handling HTTP requests and responses


@app.route("/login", methods=["POST"])
def login():
    