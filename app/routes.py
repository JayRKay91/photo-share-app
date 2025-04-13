import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif

main = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


@main.route("/")
def index():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    images = sorted(os.listdir(upload_folder), key=lambda x: os.path.getmtime(os.path.join(upload_folder, x)), reverse=True)
    descriptions = load_json(os.path.join("app", "descriptions.json"))
    albums = load_json(os.path.join("app", "albums.json"))

    return render_template("gallery.html", images=images, descriptions=descriptions, albums=albums)


@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "photos" not in request.files:
            flash("No file part")
            return redirect(request.url)

        files = request.files.getlist("photos")
        success_count = 0

        for file in files:
            if file.filename == "" or not allowed_file(file.filename):
                continue

            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower()
            save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

            if file_ext == "heic":
                try:
                    heif_file = pillow_heif.read_heif(file.stream)
                    image = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data, "raw")
                    filename = filename.rsplit('.', 1)[0] + ".jpg"
                    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                    image.save(save_path, format="JPEG")
                    success_count += 1
                except Exception as e:
                    flash(f"Failed to convert HEIC file: {e}")
                    continue
            else:
                file.save(save_path)
                success_count += 1

        flash(f"{success_count} file(s) uploaded successfully!")
        return redirect(url_for("main.index"))

    return render_template("upload.html")


@main.route("/delete/<filename>", methods=["POST"])
def delete_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} deleted successfully.")
        
        desc_path = os.path.join("app", "descriptions.json")
        album_path = os.path.join("app", "albums.json")

        descriptions = load_json(desc_path)
        albums = load_json(album_path)

        if filename in descriptions:
            del descriptions[filename]
            save_json(desc_path, descriptions)

        if filename in albums:
            del albums[filename]
            save_json(album_path, albums)

    else:
        flash(f"{filename} not found.")

    return redirect(url_for("main.index"))


@main.route("/download/<filename>")
def download_image(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)


@main.route("/description/<filename>", methods=["POST"])
def update_description(filename):
    desc_path = os.path.join("app", "descriptions.json")
    descriptions = load_json(desc_path)

    description = request.form.get("description", "").strip()
    descriptions[filename] = description
    save_json(desc_path, descriptions)

    flash("Description updated.")
    return redirect(url_for("main.index"))


@main.route("/album/<filename>", methods=["POST"])
def update_album(filename):
    album_path = os.path.join("app", "albums.json")
    albums = load_json(album_path)

    album = request.form.get("album", "").strip()
    albums[filename] = album
    save_json(album_path, albums)

    flash("Album assigned.")
    return redirect(url_for("main.index"))
