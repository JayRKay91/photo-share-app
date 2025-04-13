import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)

# Allowed image extensions (including HEIC)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'heic'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route("/")
def index():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    images = [
        f for f in os.listdir(upload_folder)
        if f.lower().endswith(tuple(ALLOWED_EXTENSIONS))
    ]

    return render_template("gallery.html", images=images)

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "photo" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["photo"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            return redirect(url_for("main.index"))
        else:
            flash("Invalid file type.")
            return redirect(request.url)

    return render_template("upload.html")

@main.route("/delete/<filename>", methods=["POST"])
def delete_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} deleted successfully.")
    else:
        flash(f"{filename} not found.")

    return redirect(url_for("main.index"))
