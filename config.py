import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Base de datos MySQL ───────────────────────────
    MYSQL_HOST     = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER     = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB       = os.environ.get("MYSQL_DB", "railway")
    MYSQL_PORT     = int(os.environ.get("MYSQL_PORT", 3307))

    # ── Flask ─────────────────────────────────────────
    SECRET_KEY  = os.environ.get("SECRET_KEY", "965620d4586d509143704365f11f1b2055f3a02a78d30311548595a62a13d936")
    DEBUG       = os.environ.get("FLASK_DEBUG", "True") == "True"

    # ── Sesión ────────────────────────────────────────
    SESSION_PERMANENT          = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)   # sesión dura 8 horas
    SESSION_COOKIE_HTTPONLY    = True                 # no accesible desde JS
    SESSION_COOKIE_SAMESITE    = "Lax"

    # ── Aplicación ────────────────────────────────────
    APP_NAME    = "EPS Citas"
    APP_VERSION = "2.0.0"
