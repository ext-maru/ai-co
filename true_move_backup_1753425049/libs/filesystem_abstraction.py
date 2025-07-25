#!/usr/bin/env python3
"""
Filesystem Abstraction Layer
Phase 3: テスト環境のためのファイルシステム抽象化
"""
import json
import logging
import os
import shutil
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class VirtualFileSystem:
    """仮想ファイルシステム実装"""

    def __init__(self, root_path: Optional[str] = None):
        """初期化メソッド"""
        self.root = Path(root_path) if root_path else Path(tempfile.mkdtemp())
        self.files: Dict[str, bytes] = {}
        self.directories: set = {"/"}
        self.metadata: Dict[str, Dict] = {}
        self.locks = threading.Lock()
        self._ensure_root()

    def _ensure_root(self):
        """ルートディレクトリを確保"""
        if not self.root.exists():
            self.root.mkdir(parents=True, exist_ok=True)

    def _normalize_path(self, path: Union[str, Path]) -> str:
        """パスを正規化"""
        if isinstance(path, Path):
            path = str(path)

        # 絶対パスに変換
        if not path.startswith("/"):
            path = "/" + path

        # 重複スラッシュを削除
        while "//" in path:
            path = path.replace("//", "/")

        # 末尾のスラッシュを削除（ルート以外）
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        return path

    def exists(self, path: Union[str, Path]) -> bool:
        """ファイルまたはディレクトリが存在するか確認"""
        norm_path = self._normalize_path(path)
        return norm_path in self.files or norm_path in self.directories

    def is_file(self, path: Union[str, Path]) -> bool:
        """パスがファイルかどうか確認"""
        norm_path = self._normalize_path(path)
        return norm_path in self.files

    def is_dir(self, path: Union[str, Path]) -> bool:
        """パスがディレクトリかどうか確認"""
        norm_path = self._normalize_path(path)
        return norm_path in self.directories

    def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ):
        """ディレクトリを作成"""
        with self.locks:
            norm_path = self._normalize_path(path)

            if norm_path in self.directories:
                if not exist_ok:
                    raise FileExistsError(f"Directory already exists: {path}")
                return

            if norm_path in self.files:
                raise FileExistsError(f"Path exists as file: {path}")

            # 親ディレクトリをチェック
            parent = str(Path(norm_path).parent)
            if parent != norm_path and parent not in self.directories:
                if parents:
                    self.mkdir(parent, parents=True, exist_ok=True)
                else:
                    raise FileNotFoundError(
                        f"Parent directory does not exist: {parent}"
                    )

            self.directories.add(norm_path)
            self.metadata[norm_path] = {
                "type": "directory",
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
            }
            logger.debug(f"Directory created: {norm_path}")

    def write_text(self, path: Union[str, Path], content: str, encoding: str = "utf-8"):
        """テキストファイルを書き込み"""
        self.write_bytes(path, content.encode(encoding))

    def write_bytes(self, path: Union[str, Path], content: bytes):
        """バイナリファイルを書き込み"""
        with self.locks:
            norm_path = self._normalize_path(path)

            # 親ディレクトリを確認
            parent = str(Path(norm_path).parent)
            if parent != "/" and parent not in self.directories:
                raise FileNotFoundError(f"Parent directory does not exist: {parent}")

            self.files[norm_path] = content
            self.metadata[norm_path] = {
                "type": "file",
                "size": len(content),
                "created": datetime.now().isoformat(),
                "modified": datetime.now().isoformat(),
            }
            logger.debug(f"File written: {norm_path} ({len(content)} bytes)")

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """テキストファイルを読み込み"""
        return self.read_bytes(path).decode(encoding)

    def read_bytes(self, path: Union[str, Path]) -> bytes:
        """バイナリファイルを読み込み"""
        with self.locks:
            norm_path = self._normalize_path(path)

            if norm_path not in self.files:
                raise FileNotFoundError(f"File not found: {path}")

            return self.files[norm_path]

    def listdir(self, path: Union[str, Path] = "/") -> List[str]:
        """ディレクトリの内容をリスト"""
        with self.locks:
            norm_path = self._normalize_path(path)

            if norm_path not in self.directories:
                raise NotADirectoryError(f"Not a directory: {path}")

            items = []

            # ファイルを追加
            for file_path in self.files:
                if str(Path(file_path).parent) == norm_path:
                    items.append(Path(file_path).name)

            # サブディレクトリを追加
            for dir_path in self.directories:
                if dir_path != norm_path and str(Path(dir_path).parent) == norm_path:
                    items.append(Path(dir_path).name)

            return sorted(items)

    def remove(self, path: Union[str, Path]):
        """ファイルを削除"""
        with self.locks:
            norm_path = self._normalize_path(path)

            if norm_path in self.files:
                del self.files[norm_path]
                if norm_path in self.metadata:
                    del self.metadata[norm_path]
                logger.debug(f"File removed: {norm_path}")
            else:
                raise FileNotFoundError(f"File not found: {path}")

    def rmdir(self, path: Union[str, Path]):
        """空のディレクトリを削除"""
        with self.locks:
            norm_path = self._normalize_path(path)

            if norm_path not in self.directories:
                raise NotADirectoryError(f"Not a directory: {path}")

            if norm_path == "/":
                raise PermissionError("Cannot remove root directory")

            # ディレクトリが空かチェック
            if self.listdir(norm_path):
                raise OSError(f"Directory not empty: {path}")

            self.directories.remove(norm_path)
            if norm_path in self.metadata:
                del self.metadata[norm_path]
            logger.debug(f"Directory removed: {norm_path}")

    def copy(self, src: Union[str, Path], dst: Union[str, Path]):
        """ファイルをコピー"""
        content = self.read_bytes(src)
        self.write_bytes(dst, content)

    def move(self, src: Union[str, Path], dst: Union[str, Path]):
        """ファイルまたはディレクトリを移動"""
        with self.locks:
            src_norm = self._normalize_path(src)
            dst_norm = self._normalize_path(dst)

            if src_norm in self.files:
                # ファイルの移動
                self.files[dst_norm] = self.files[src_norm]
                del self.files[src_norm]

                if src_norm in self.metadata:
                    self.metadata[dst_norm] = self.metadata[src_norm]
                    del self.metadata[src_norm]

            elif src_norm in self.directories:
                # ディレクトリの移動（簡易実装）
                self.directories.add(dst_norm)
                self.directories.remove(src_norm)

                if src_norm in self.metadata:
                    self.metadata[dst_norm] = self.metadata[src_norm]
                    del self.metadata[src_norm]
            else:
                raise FileNotFoundError(f"Source not found: {src}")

    def get_size(self, path: Union[str, Path]) -> int:
        """ファイルサイズを取得"""
        norm_path = self._normalize_path(path)

        if norm_path in self.files:
            return len(self.files[norm_path])
        elif norm_path in self.directories:
            # ディレクトリの場合は0を返す
            return 0
        else:
            raise FileNotFoundError(f"Path not found: {path}")


class FileSystemAbstraction:
    """ファイルシステム操作の抽象化レイヤー"""

    def __init__(self, use_virtual: bool = False, root_path: Optional[str] = None):
        """初期化メソッド"""
        self.use_virtual = use_virtual
        self.vfs = VirtualFileSystem(root_path) if use_virtual else None
        self.root = Path(root_path) if root_path else Path.cwd()

    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """パスを解決"""
        if isinstance(path, str):
            path = Path(path)

        if not path.is_absolute():
            path = self.root / path

        return path

    @contextmanager
    def open(
        self, path: Union[str, Path], mode: str = "r", encoding: Optional[str] = None
    ):
        """ファイルを開く"""
        if self.use_virtual:
            # 仮想ファイルシステムの場合
            norm_path = self.vfs._normalize_path(path)

            if "r" in mode:
                if norm_path not in self.vfs.files:
                    raise FileNotFoundError(f"File not found: {path}")

                content = self.vfs.files[norm_path]
                if "b" not in mode and encoding:
                    content = content.decode(encoding or "utf-8")

                from io import BytesIO, StringIO

                yield StringIO(content) if "b" not in mode else BytesIO(content)
            else:
                # 書き込みモード
                from io import BytesIO, StringIO

                buffer = StringIO() if "b" not in mode else BytesIO()

                try:
                    yield buffer
                    content = buffer.getvalue()
                    if isinstance(content, str):
                        content = content.encode(encoding or "utf-8")
                    self.vfs.write_bytes(norm_path, content)
                finally:
                    buffer.close()
        else:
            # 実際のファイルシステム
            resolved_path = self._resolve_path(path)
            with open(resolved_path, mode, encoding=encoding) as f:
                yield f

    def exists(self, path: Union[str, Path]) -> bool:
        """パスが存在するか確認"""
        if self.use_virtual:
            return self.vfs.exists(path)
        return self._resolve_path(path).exists()

    def is_file(self, path: Union[str, Path]) -> bool:
        """ファイルかどうか確認"""
        if self.use_virtual:
            return self.vfs.is_file(path)
        return self._resolve_path(path).is_file()

    def is_dir(self, path: Union[str, Path]) -> bool:
        """ディレクトリかどうか確認"""
        if self.use_virtual:
            return self.vfs.is_dir(path)
        return self._resolve_path(path).is_dir()

    def mkdir(
        self, path: Union[str, Path], parents: bool = False, exist_ok: bool = False
    ):
        """ディレクトリを作成"""
        if self.use_virtual:
            self.vfs.mkdir(path, parents=parents, exist_ok=exist_ok)
        else:
            self._resolve_path(path).mkdir(parents=parents, exist_ok=exist_ok)

    def read_text(self, path: Union[str, Path], encoding: str = "utf-8") -> str:
        """テキストファイルを読み込み"""
        if self.use_virtual:
            return self.vfs.read_text(path, encoding)
        return self._resolve_path(path).read_text(encoding=encoding)

    def write_text(self, path: Union[str, Path], content: str, encoding: str = "utf-8"):
        """テキストファイルを書き込み"""
        if self.use_virtual:
            self.vfs.write_text(path, content, encoding)
        else:
            self._resolve_path(path).write_text(content, encoding=encoding)

    def read_json(self, path: Union[str, Path]) -> Any:
        """JSONファイルを読み込み"""
        content = self.read_text(path)
        return json.loads(content)

    def write_json(self, path: Union[str, Path], data: Any, indent: int = 2):
        """JSONファイルを書き込み"""
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        self.write_text(path, content)

    def remove(self, path: Union[str, Path]):
        """ファイルを削除"""
        if self.use_virtual:
            self.vfs.remove(path)
        else:
            self._resolve_path(path).unlink()

    def rmdir(self, path: Union[str, Path]):
        """ディレクトリを削除"""
        if self.use_virtual:
            self.vfs.rmdir(path)
        else:
            self._resolve_path(path).rmdir()

    def rmtree(self, path: Union[str, Path]):
        """ディレクトリツリーを削除"""
        if self.use_virtual:
            # 簡易実装
            norm_path = self.vfs._normalize_path(path)
            if not self.vfs.is_dir(norm_path):
                raise NotADirectoryError(f"Not a directory: {path}")

            # 再帰的に削除
            for item in list(self.vfs.listdir(norm_path)):
                item_path = Path(norm_path) / item
                if self.vfs.is_dir(str(item_path)):
                    self.rmtree(str(item_path))
                else:
                    self.vfs.remove(str(item_path))

            self.vfs.rmdir(norm_path)
        else:
            shutil.rmtree(self._resolve_path(path))

    def copy(self, src: Union[str, Path], dst: Union[str, Path]):
        """ファイルをコピー"""
        if self.use_virtual:
            self.vfs.copy(src, dst)
        else:
            shutil.copy2(self._resolve_path(src), self._resolve_path(dst))

    def move(self, src: Union[str, Path], dst: Union[str, Path]):
        """ファイルを移動"""
        if self.use_virtual:
            self.vfs.move(src, dst)
        else:
            shutil.move(self._resolve_path(src), self._resolve_path(dst))

    def listdir(self, path: Union[str, Path] = ".") -> List[str]:
        """ディレクトリの内容をリスト"""
        if self.use_virtual:
            return self.vfs.listdir(path)
        return os.listdir(self._resolve_path(path))

    def glob(self, pattern: str) -> List[Path]:
        """パターンにマッチするファイルを検索"""
        if self.use_virtual:
            # 簡易実装
            results = []
            # TODO: より完全なglob実装
            return results
        else:
            return list(self.root.glob(pattern))

    @contextmanager
    def temp_dir(self):
        """一時ディレクトリを作成"""
        if self.use_virtual:
            temp_name = f"/tmp/{uuid.uuid4()}"
            self.vfs.mkdir(temp_name, parents=True)
            try:
                yield temp_name
            finally:
                try:
                    self.rmtree(temp_name)
                except:
                    pass
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                yield tmpdir


# グローバルインスタンス
_fs = FileSystemAbstraction()


# 便利な関数をエクスポート
def set_filesystem(fs: FileSystemAbstraction):
    """ファイルシステムを設定"""
    global _fs
    _fs = fs


def get_filesystem() -> FileSystemAbstraction:
    """現在のファイルシステムを取得"""
    return _fs


# よく使う関数のショートカット
open = lambda *args, **kwargs: _fs.open(*args, **kwargs)
exists = lambda path: _fs.exists(path)
is_file = lambda path: _fs.is_file(path)
is_dir = lambda path: _fs.is_dir(path)
mkdir = lambda *args, **kwargs: _fs.mkdir(*args, **kwargs)
read_text = lambda *args, **kwargs: _fs.read_text(*args, **kwargs)
write_text = lambda *args, **kwargs: _fs.write_text(*args, **kwargs)
read_json = lambda *args, **kwargs: _fs.read_json(*args, **kwargs)
write_json = lambda *args, **kwargs: _fs.write_json(*args, **kwargs)

__all__ = [
    "FileSystemAbstraction",
    "VirtualFileSystem",
    "set_filesystem",
    "get_filesystem",
    "open",
    "exists",
    "is_file",
    "is_dir",
    "mkdir",
    "read_text",
    "write_text",
    "read_json",
    "write_json",
]
