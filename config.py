import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Base de datos MySQL ───────────────────────────
    MYSQL_HOST     = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER     = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB       = os.environ.get("MYSQL_DB", "eps_citas")
    MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3306))

    # ── Flask ─────────────────────────────────────────
    SECRET_KEY  = os.environ.get("SECRET_KEY", "eps_citas_secret_key_dev")
    DEBUG       = os.environ.get("FLASK_DEBUG", "True") == "True"

    # ── Sesión ────────────────────────────────────────
    SESSION_PERMANENT          = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)   # sesión dura 8 horas
    SESSION_COOKIE_HTTPONLY    = True                 # no accesible desde JS
    SESSION_COOKIE_SAMESITE    = "Lax"

    # ── Aplicación ────────────────────────────────────
    APP_NAME    = "EPS Citas"
    APP_VERSION = "2.0.0"
