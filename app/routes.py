import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)

@main.route("/")
def index():
    images = os.listdir(current_app.config["UPLOAD_FOLDER"])
    return render_template("gallery.html", images=images)

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files["photo"]
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            return redirect(url_for("main.index"))
    return render_template("upload.html")
