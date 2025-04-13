import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif
from datetime import datetime

main = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_descriptions():
    path = os.path.join(current_app.root_path, 'descriptions.json')
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def save_descriptions(data):
    path = os.path.join(current_app.root_path, 'descriptions.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

@main.route("/")
def index():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    images = os.listdir(upload_folder)
    images.sort(key=lambda x: os.path.getmtime(os.path.join(upload_folder, x)), reverse=True)
    descriptions = load_descriptions()
    return render_template("gallery.html", images=images, descriptions=descriptions)

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "photos" not in request.files:
            flash("No file part")
            return redirect(request.url)

        files = request.files.getlist("photos")
        uploaded = 0

        for file in files:
            if file and allowed_file(file.filename):
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
                    except Exception as e:
                        flash(f"Failed to convert HEIC file: {e}")
                        continue
                else:
                    file.save(save_path)

                uploaded += 1

        if uploaded:
            flash(f"{uploaded} file(s) uploaded successfully!")
        else:
            flash("No valid files uploaded.")

        return redirect(url_for("main.index"))

    return render_template("upload.html")

@main.route("/delete/<filename>", methods=["POST"])
def delete_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} deleted successfully.")
        descriptions = load_descriptions()
        if filename in descriptions:
            del descriptions[filename]
            save_descriptions(descriptions)
    else:
        flash(f"{filename} not found.")

    return redirect(url_for("main.index"))

@main.route("/download/<filename>")
def download_image(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename, as_attachment=True)

@main.route("/describe/<filename>", methods=["POST"])
def update_description(filename):
    new_desc = request.form.get("description", "").strip()
    descriptions = load_descriptions()
    descriptions[filename] = new_desc
    save_descriptions(descriptions)
    flash("Description updated!")
    return redirect(url_for("main.index"))
