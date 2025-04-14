import os
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif
from moviepy.editor import VideoFileClip

main = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic", "mp4", "mov", "webm"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def is_video(filename):
    return filename.lower().endswith((".mp4", ".mov", ".webm"))

def generate_video_thumbnail(video_path, thumb_path):
    try:
        clip = VideoFileClip(video_path)
        frame = clip.get_frame(1)  # Grab frame at 1 second
        image = Image.fromarray(frame)
        image.save(thumb_path, "JPEG")
        clip.close()
    except Exception as e:
        print(f"Error generating thumbnail: {e}")

@main.route("/")
def index():
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    thumb_folder = os.path.join(current_app.static_folder, "thumbnails")

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(thumb_folder, exist_ok=True)

    # Load metadata
    def load_json(path, default={}):
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default, f)
        with open(path, "r") as f:
            return json.load(f)

    descriptions = load_json(os.path.join(current_app.root_path, "descriptions.json"))
    albums = load_json(os.path.join(current_app.root_path, "albums.json"))

    selected_album = request.args.get("album")
    all_files = os.listdir(upload_folder)

    if selected_album and selected_album in albums:
        files = albums[selected_album]
    else:
        files = all_files

    files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(upload_folder, x)), reverse=True)

    images = []
    for f in files:
        file_type = "video" if is_video(f) else "image"
        thumb_name = f"{f}.jpg"
        thumb_path = os.path.join("thumbnails", thumb_name)

        if file_type == "video":
            full_thumb_path = os.path.join(thumb_folder, thumb_name)
            if not os.path.exists(full_thumb_path):
                generate_video_thumbnail(os.path.join(upload_folder, f), full_thumb_path)

        images.append({
            "filename": f,
            "type": file_type,
            "thumb": thumb_path,
            "description": descriptions.get(f, "")
        })

    return render_template("gallery.html", images=images, albums=albums)

@main.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "photos" not in request.files:
            flash("No file part")
            return redirect(request.url)

        files = request.files.getlist("photos")
        album = request.form.get("album", "Default")
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        albums_path = os.path.join(current_app.root_path, "albums.json")
        os.makedirs(upload_folder, exist_ok=True)

        # Load albums
        albums = {}
        if os.path.exists(albums_path):
            with open(albums_path, "r") as f:
                albums = json.load(f)

        uploaded_filenames = []

        for file in files:
            if file.filename == "" or not allowed_file(file.filename):
                continue

            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1].lower()
            save_path = os.path.join(upload_folder, filename)

            if ext == "heic":
                try:
                    heif = pillow_heif.read_heif(file.stream)
                    img = Image.frombytes(heif.mode, heif.size, heif.data, "raw")
                    filename = filename.rsplit('.', 1)[0] + ".jpg"
                    save_path = os.path.join(upload_folder, filename)
                    img.save(save_path, format="JPEG")
                    flash(f"{filename} (converted from HEIC) uploaded.")
                except Exception as e:
                    flash(f"Failed to convert HEIC file: {e}")
                    continue

            elif ext == "mov":
                try:
                    temp_path = os.path.join(upload_folder, filename)
                    file.save(temp_path)
                    filename = filename.rsplit('.', 1)[0] + ".mp4"
                    save_path = os.path.join(upload_folder, filename)
                    clip = VideoFileClip(temp_path)
                    clip.write_videofile(save_path, codec="libx264", audio_codec="aac")
                    os.remove(temp_path)
                    clip.close()
                    flash(f"{filename} (converted from MOV) uploaded.")
                except Exception as e:
                    flash(f"Failed to convert MOV file: {e}")
                    continue

            else:
                file.save(save_path)
                flash(f"{filename} uploaded.")

            uploaded_filenames.append(filename)

        # Update album
        if album not in albums:
            albums[album] = []
        albums[album].extend(uploaded_filenames)

        with open(albums_path, "w") as f:
            json.dump(albums, f)

        return redirect(url_for("main.index"))

    return render_template("upload.html")

@main.route("/download/<filename>")
def download_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(upload_folder, filename, as_attachment=True)

@main.route("/delete/<filename>", methods=["POST"])
def delete_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} deleted.")
    return redirect(url_for("main.index"))

@main.route("/description/<filename>", methods=["POST"])
def update_description(filename):
    new_description = request.form.get("description", "")
    path = os.path.join(current_app.root_path, "descriptions.json")
    descriptions = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            descriptions = json.load(f)
    descriptions[filename] = new_description
    with open(path, "w") as f:
        json.dump(descriptions, f)
    flash(f"Description updated for {filename}")
    return redirect(url_for("main.index"))
