import os
from datetime import timedelta
from dotenv import load_dotenv

# Carga .env en desarrollo local; en Railway las vars ya están en el entorno
load_dotenv()


class Config:
    # ── Base de datos ─────────────────────────────
    # Railway inyecta MYSQLHOST, MYSQLUSER, MYSQLPASSWORD, MYSQLDATABASE, MYSQLPORT
    # También soportamos los nombres personalizados del .env local
    MYSQL_HOST     = (os.environ.get("MYSQLHOST")
                      or os.environ.get("MYSQL_HOST")
                      or "localhost")

    MYSQL_USER     = (os.environ.get("MYSQLUSER")
                      or os.environ.get("MYSQL_USER")
                      or "root")

    MYSQL_PASSWORD = (os.environ.get("MYSQLPASSWORD")
                      or os.environ.get("MYSQL_PASSWORD")
                      or "")

    MYSQL_DB       = (os.environ.get("MYSQLDATABASE")
                      or os.environ.get("MYSQL_DATABASE")
                      or os.environ.get("MYSQL_DB")
                      or "railway")

    MYSQL_PORT     = int(os.environ.get("MYSQLPORT")
                         or os.environ.get("MYSQL_PORT")
                         or 3306)

    # ── Flask ─────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "53082cfd47760e8350c200b34253f530c8f944a8add321016147441da50f9662")
    DEBUG      = os.environ.get("FLASK_DEBUG", "False") == "True"

    # ── Sesión ────────────────────────────────────
    SESSION_PERMANENT          = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # ── App ───────────────────────────────────────
    APP_NAME    = "EPS Citas"
    APP_VERSION = "2.0.0"
