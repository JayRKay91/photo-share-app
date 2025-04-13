import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)

@main.route("/")
def index():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    images = os.listdir(upload_folder)
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

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            return redirect(url_for("main.index"))

    return render_template("upload.html")
