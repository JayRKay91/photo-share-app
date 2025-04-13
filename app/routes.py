import os
from flask import Blueprint, render_template, current_app

main = Blueprint("main", __name__)

@main.route("/")
def index():
    # Ensure upload folder exists
    uploads_path = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(uploads_path, exist_ok=True)

    # Get list of image filenames
    images = os.listdir(uploads_path)
    images = [f for f in images if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"))]

    return render_template("gallery.html", images=images)
