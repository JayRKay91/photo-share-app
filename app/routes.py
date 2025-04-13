import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import pillow_heif

main = Blueprint("main", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "heic"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
        if "photos" not in request.files:
            flash("No file part")
            return redirect(request.url)

        files = request.files.getlist("photos")
        if not files or files[0].filename == "":
            flash("No selected files")
            return redirect(request.url)

        success_count = 0

        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_ext = filename.rsplit('.', 1)[1].lower()
                save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

                if file_ext == "heic":
                    try:
                        heif_file = pillow_heif.read_heif(file.stream)
                        image = Image.frombytes(
                            heif_file.mode, heif_file.size, heif_file.data, "raw"
                        )
                        filename = filename.rsplit('.', 1)[0] + ".jpg"
                        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                        image.save(save_path, format="JPEG")
                        success_count += 1
                    except Exception as e:
                        flash(f"Failed to convert {file.filename}: {e}")
                        continue
                else:
                    file.save(save_path)
                    success_count += 1

        if success_count:
            flash(f"{success_count} file(s) uploaded successfully!")
        else:
            flash("No valid images were uploaded.")
        return redirect(url_for("main.index"))

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
