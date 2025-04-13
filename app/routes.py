import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif

main = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {}


def save_json(data, file_path):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


@main.route("/")
def index():
    upload_folder = current_app.config["UPLOAD_FOLDER"]

    # ✅ Ensure uploads folder exists
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    descriptions_path = os.path.join("app", "descriptions.json")
    albums_path = os.path.join("app", "albums.json")

    descriptions = load_json(descriptions_path)
    albums = load_json(albums_path)

    images = []
    for filename in os.listdir(upload_folder):
        file_info = {"filename": filename}
        file_info["description"] = descriptions.get(filename, "")
        file_info["album"] = albums.get(filename, "")
        images.append(file_info)

    images.sort(key=lambda img: os.path.getmtime(os.path.join(upload_folder, img["filename"])), reverse=True)

    return render_template("gallery.html", images=images, descriptions=descriptions, albums=albums)


@main.route("/upload", methods=["GET", "POST"])
def upload():
    descriptions_path = os.path.join("app", "descriptions.json")
    albums_path = os.path.join("app", "albums.json")

    descriptions = load_json(descriptions_path)
    albums = load_json(albums_path)

    upload_folder = current_app.config["UPLOAD_FOLDER"]

    if request.method == "POST":
        if "photos" not in request.files:
            flash("No file part")
            return redirect(request.url)

        files = request.files.getlist("photos")
        selected_album = request.form.get("album")
        new_album = request.form.get("new_album")

        if new_album:
            album_name = new_album.strip()
        else:
            album_name = selected_album.strip() if selected_album else ""

        upload_count = 0

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                save_path = os.path.join(upload_folder, filename)

                if file_ext == "heic":
                    try:
                        heif_file = pillow_heif.read_heif(file.stream)
                        image = Image.frombytes(
                            heif_file.mode, heif_file.size, heif_file.data, "raw"
                        )
                        filename = filename.rsplit('.', 1)[0] + ".jpg"
                        save_path = os.path.join(upload_folder, filename)
                        image.save(save_path, format="JPEG")
                        flash(f"{filename} converted from HEIC and uploaded.")
                    except Exception as e:
                        flash(f"Failed to convert HEIC file: {e}")
                        continue
                else:
                    file.save(save_path)
                    flash(f"{filename} uploaded successfully.")

                if album_name:
                    albums[filename] = album_name

                upload_count += 1

        save_json(descriptions, descriptions_path)
        save_json(albums, albums_path)

        flash(f"{upload_count} file(s) uploaded successfully!")
        return redirect(url_for("main.index"))

    existing_albums = list(set(albums.values()))
    return render_template("upload.html", albums=existing_albums)


@main.route("/delete/<filename>", methods=["POST"])
def delete_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)

    descriptions_path = os.path.join("app", "descriptions.json")
    albums_path = os.path.join("app", "albums.json")

    descriptions = load_json(descriptions_path)
    albums = load_json(albums_path)

    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} deleted successfully.")
        descriptions.pop(filename, None)
        albums.pop(filename, None)
    else:
        flash(f"{filename} not found.")

    save_json(descriptions, descriptions_path)
    save_json(albums, albums_path)

    return redirect(url_for("main.index"))


@main.route("/description/<filename>", methods=["POST"])
def update_description(filename):
    descriptions_path = os.path.join("app", "descriptions.json")
    descriptions = load_json(descriptions_path)

    description = request.form.get("description", "").strip()
    if description:
        descriptions[filename] = description
        flash(f"Description for {filename} updated.")
    else:
        descriptions.pop(filename, None)
        flash(f"Description for {filename} removed.")

    save_json(descriptions, descriptions_path)
    return redirect(url_for("main.index"))
