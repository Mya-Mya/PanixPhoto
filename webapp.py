from flask import (
    Flask,
    request,
    jsonify,
    render_template,
    send_from_directory,
    redirect,
    url_for,
)
from pathlib import Path
import uuid
from argparse import ArgumentParser
from repository import *

app = Flask(__name__, template_folder="./WebappTemplates")

UPLOAD_TEMP_DIR = Path("./UploadTemp")
UPLOAD_TEMP_DIR.mkdir(parents=True, exist_ok=True)

media_repository = MediaRepository()


def make_success_response(message: str, code: int = 200):
    return jsonify({"message": message}), code


def make_error_response(message: str, code: int = 400):
    return jsonify({"error": message}), code


def safely_send_file(target: Path):
    return send_from_directory(target.parent, target.name)


@app.get("/app/", defaults={"dir_path": ""})
@app.get("/app/<dir_path>")
def handle_app_(dir_path: str):
    relative_dir_path = Path(dir_path)
    items = media_repository.list_items(relative_dir_path)

    srcs = []
    for item in items:
        if item.type != "Media":
            continue
        payload: MediaPayload = item.payload
        if payload.type != "Image":
            continue
        srcs.append("/api/media/" + dir_path + "/" + payload.filename)
    return render_template(
        "list.html", current_directory=relative_dir_path.name, srcs=srcs
    )


@app.get("/api/media/<path>")
def handle_api_media_(path):
    relative_path = Path(path)
    resolved = media_repository.safely_resolve(relative_path)
    if not resolved:
        return make_error_response(f"パス {path} が見つかりませんでした"), 404
    return safely_send_file(resolved)


@app.post("/api/upload")
def handle_api_upload():
    if "file" not in request.files:
        return make_error_response("ファイルが選択されていません")
    file = request.files["file"]
    if file.filename == "":
        return make_error_response("ファイル名が指定されていません")
    tmp_path = UPLOAD_TEMP_DIR / (uuid.uuid4().hex + str(file.filename))
    file.save(str(tmp_path))
    success = media_repository.add_media(tmp_path, str(file.filename))

    if not success and tmp_path.exists():
        tmp_path.unlink()
    if success:
        return make_success_response("アップロードに成功しました")
    else:
        return make_error_response("アップロードに失敗しました")


if __name__ == "__main__":
    parser = ArgumentParser(prog="PanixPhoto Web Server")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    app.run("0.0.0.0", int(args.port), debug=True)
