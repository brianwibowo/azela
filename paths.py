"""Resolusi path untuk mode development dan executable PyInstaller."""

from pathlib import Path
import sys


def is_frozen() -> bool:
    """Mengembalikan True jika aplikasi berjalan dari bundle PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Folder tempat executable (.exe) atau root proyek berada (lokasi azela.db)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    """Folder tempat aset statis (web/) dibundel atau berada saat dev."""
    if is_frozen() and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def db_path() -> Path:
    """Path lengkap ke file database SQLite lokal."""
    return app_dir() / "azela.db"


def web_dir() -> Path:
    """Path lengkap ke folder frontend HTML/CSS/JS."""
    return resource_dir() / "web"

