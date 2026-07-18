from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Literal
import datetime
import shutil

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}


@dataclass
class DirectoryPayload:
    name: str


@dataclass
class MediaPayload:
    type: Literal["Image", "Video"]
    filename: str
    createdat_iso: str
    updateat_iso: str
    size: int


@dataclass
class Item:
    type: Literal["Directory", "Media"]
    payload: DirectoryPayload | MediaPayload

    def to_dict(self):
        return {"type": self.type, "payload": asdict(self.payload)}

class MediaRepository:
    def __init__(self, config: dict = dict()) -> None:
        self.config = config
        self.root = Path(self.config.get("rootPath", "./Data")).absolute()

    def safely_resolve(self, relative_path: Path) -> Path | None:
        if relative_path.is_absolute():
            return None
        try:
            target = (self.root / relative_path).resolve()
            if self.root in target.parents or target == self.root:
                return target
            return None
        except Exception:
            return None

    def _parse_directory(self, target: Path) -> Item:
        return Item(type="Directory", payload=DirectoryPayload(name=target.name))

    def _parse_file(self, target: Path) -> Item | None:
        ext = target.suffix.lower()
        media_type = None
        if ext in IMAGE_EXTENSIONS:
            media_type = "Image"
        elif ext in VIDEO_EXTENSIONS:
            media_type = "Video"
        if media_type is None:
            return None
        try:
            stat = target.stat()
            createdat_iso = datetime.datetime.fromtimestamp(stat.st_ctime).isoformat()
            updateat_iso = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
            return Item(
                type="Media",
                payload=MediaPayload(
                    type=media_type,
                    filename=target.name,
                    createdat_iso=createdat_iso,
                    updateat_iso=updateat_iso,
                    size=stat.st_size,
                ),
            )
        except:
            return None

    def list_items(self, relative_dir_path: Path) -> list[Item]:
        dir = self.safely_resolve(relative_dir_path)
        if dir is None or not dir.is_dir():
            return []
        items = []
        for target in dir.iterdir():
            if target.name.startswith("."):
                continue
            if target.is_dir():
                items.append(self._parse_directory(target))
            elif target.is_file():
                maybe_item = self._parse_file(target)
                if maybe_item is not None:
                    items.append(maybe_item)
        return items

    def rename_media_basename(
        self, relative_target_path: Path, new_basename: str
    ) -> bool:
        target = self.safely_resolve(relative_target_path)
        if target is None:
            return False
        if not target.is_file():
            return False

        new_filename = f"{new_basename}{target.suffix}"
        new_path = target.parent / new_filename
        if new_path.exists():
            return False
        target.rename(new_path)
        return True

    def delete_item(self, relative_target_path: Path) -> bool:
        target = self.safely_resolve(relative_target_path)
        if target is None:
            return False
        if not target.is_file():
            return False
        if not target.exists():
            return False
        try:
            target.unlink()
            return True
        except Exception:
            return False

    def add_media(self, src: Path, relative_dst_path: Path) -> bool:
        if not src.exists():
            return False
        ext = Path(relative_dst_path).suffix.lower()
        if ext not in IMAGE_EXTENSIONS and ext not in VIDEO_EXTENSIONS:
            return False
        dest = self.safely_resolve(relative_dst_path)
        if dest is None:
            return False
        if dest.exists():
            return False
        try:
            shutil.move(str(src), str(dest))
            return True
        except Exception:
            return False


if __name__ == "__main__":
    media_repository = MediaRepository()
    current_directory = Path("./")
    while True:
        input_content = input(str(current_directory) + " : ")
        if input_content == "exit":
            break
        if input_content == "ls":
            print(media_repository.list_items(current_directory))
