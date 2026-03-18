# 🏥 EPS Citas — Guía de Instalación Local

Sistema web de gestión de citas médicas desarrollado con **Python + Flask + MySQL**.

---

## ✅ Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente:

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| Python | 3.9 o superior | https://www.python.org/downloads/ |
| MySQL Server | 8.0 o superior | https://dev.mysql.com/downloads/mysql/ |
| Git (opcional) | cualquiera | https://git-scm.com/ |

> 💡 También puedes usar **XAMPP** (incluye MySQL): https://www.apachefriends.org/

---

## 📁 Estructura del Proyecto

```
eps_citas_app/
├── app.py                  ← Punto de entrada Flask (rutas)
├── config.py               ← Configuración (lee el .env)
├── database.py             ← Gestión de conexión MySQL
├── requirements.txt        ← Dependencias Python
├── .env                    ← Variables de entorno (NO subir a Git)
├── .env.example            ← Plantilla del .env (sí subir a Git)
├── .gitignore
├── eps_citas_db.sql        ← Script para crear la base de datos
├── models/
│   ├── __init__.py
│   ├── pacientes.py        ← CRUD pacientes + validaciones
│   └── citas.py            ← CRUD citas + validaciones
├── templates/
│   ├── base.html           ← Layout base (navbar, footer)
│   ├── index.html          ← Página principal
│   ├── registro_paciente.html
│   ├── reservar_cita.html
│   ├── consulta_cita.html
│   ├── resultado_cita.html
│   └── error.html
└── static/
    ├── css/style.css       ← Estilos propios (diseño médico)
    └── js/main.js          ← Validaciones y UI
```

---

## 🚀 Instalación Paso a Paso

### Paso 1 — Descargar el proyecto

```bash
# Opción A: clonar con Git
git clone <url-del-repositorio>
cd eps_citas_app

# Opción B: descargar el ZIP y descomprimirlo, luego:
cd eps_citas_app
```

---

### Paso 2 — Crear el entorno virtual

```bash
# Crear el entorno virtual
python -m venv venv

# Activarlo en Windows (CMD o PowerShell):
venv\Scripts\activate

# Activarlo en Mac / Linux:
source venv/bin/activate
```

> Sabrás que está activo porque el prompt cambia a `(venv)`.

---

### Paso 3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

Esto instala:
- `Flask 3.0` — framework web
- `mysql-connector-python` — conexión a MySQL
- `python-dotenv` — carga el archivo `.env`

---

### Paso 4 — Configurar las variables de entorno

Copia el archivo `.env.example` y renómbralo a `.env`:

```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Abre el archivo `.env` con cualquier editor y completa tus datos:

```env
# ── Base de datos ─────────────────────────────
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=tu_contraseña_de_mysql    # ← CAMBIA ESTO
MYSQL_DB=eps_citas

# ── Flask ──────────────────────────────────────
SECRET_KEY=pega_aqui_la_clave_generada   # ← CAMBIA ESTO
FLASK_DEBUG=True
FLASK_ENV=development
```

**Generar una SECRET_KEY segura:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y pégalo en `SECRET_KEY=` del `.env`.

---

### Paso 5 — Crear la base de datos MySQL

#### Opción A: desde la terminal de MySQL

```bash
# Abrir MySQL en la terminal
mysql -u root -p

# Dentro de MySQL, ejecutar el script:
source ruta/completa/eps_citas_app/eps_citas_db.sql

# Verificar que se creó correctamente:
USE eps_citas;
SHOW TABLES;
# Debe mostrar: citas | pacientes
```

#### Opción B: desde phpMyAdmin (XAMPP)

1. Abre `http://localhost/phpmyadmin`
2. Haz clic en **Importar** (pestaña superior)
3. Selecciona el archivo `eps_citas_db.sql`
4. Clic en **Continuar**

#### Opción C: desde MySQL Workbench

1. Abre MySQL Workbench y conecta a tu servidor local
2. Menú **File → Open SQL Script**
3. Selecciona `eps_citas_db.sql`
4. Ejecuta con **Ctrl + Shift + Enter** (ejecutar todo)

---

### Paso 6 — Ejecutar la aplicación

```bash
# Asegúrate de tener el entorno virtual activo (venv)
python app.py
```

Deberías ver en la terminal:

```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

Abre el navegador en: **http://localhost:5000** 🎉

---

## 🌐 Rutas de la Aplicación

| Ruta | Método | Descripción |
|---|---|---|
| `/` | GET | Página principal |
| `/registro-paciente` | GET, POST | Registrar nuevo paciente |
| `/reservar-cita` | GET, POST | Reservar cita médica |
| `/consulta-cita` | GET, POST | Buscar citas por documento |
| `/resultado-cita/<doc>` | GET | Ver citas de un paciente |
| `/actualizar-cita/<id>` | GET, POST | Editar una cita existente |
| `/cancelar-cita/<id>` | POST | Cancelar (eliminar) una cita |

---

## 🗄️ Esquema de la Base de Datos

```sql
-- Tabla pacientes
CREATE TABLE pacientes (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  documento VARCHAR(15) NOT NULL UNIQUE,
  nombre    VARCHAR(80) NOT NULL,
  apellido  VARCHAR(80) NOT NULL,
  telefono  VARCHAR(20) NOT NULL,
  correo    VARCHAR(100) NOT NULL,
  eps       VARCHAR(100) NOT NULL,
  creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla citas (relacionada con pacientes)
CREATE TABLE citas (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  documento     VARCHAR(15) NOT NULL,
  medico        VARCHAR(100) NOT NULL,
  tipo_cita     ENUM('General','Odontología','Especialista') NOT NULL,
  fecha         DATE NOT NULL,
  hora          TIME NOT NULL,
  direccion_eps VARCHAR(150) NOT NULL,
  creado_en     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (documento) REFERENCES pacientes(documento)
    ON DELETE CASCADE ON UPDATE CASCADE
);
```

---

## ⚠️ Solución de Problemas Comunes

### ❌ Error: `ModuleNotFoundError: No module named 'flask'`
El entorno virtual no está activo. Ejecuta:
```bash
# Windows:   venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
```

### ❌ Error: `mysql.connector.errors.DatabaseError: 1049 Unknown database 'eps_citas'`
La base de datos no fue creada. Ejecuta el script SQL (Paso 5).

### ❌ Error: `Access denied for user 'root'@'localhost'`
La contraseña en `.env` es incorrecta. Revisa `MYSQL_PASSWORD=` en tu archivo `.env`.

### ❌ Error: `Can't connect to MySQL server`
MySQL no está corriendo. Inicia el servidor:
- **Windows**: Abre el panel de XAMPP y presiona **Start** en MySQL, o abre `services.msc` y arranca `MySQL80`.
- **Mac**: `sudo /usr/local/mysql/support-files/mysql.server start`
- **Linux**: `sudo systemctl start mysql`

### ❌ La página abre pero muestra "Base de datos: Sin conexión"
Revisa que los valores del `.env` sean correctos y que MySQL esté activo.

---

## 🔒 Seguridad — Buenas Prácticas

- **Nunca** subas el archivo `.env` a GitHub. Ya está en `.gitignore`.
- En producción, cambia `FLASK_DEBUG=False`.
- Genera siempre una `SECRET_KEY` aleatoria y única por entorno.
- El archivo `.env.example` (sin contraseñas reales) sí puede subirse al repositorio.

---

## 📦 Dependencias

```
Flask==3.0.3
mysql-connector-python==8.4.0
python-dotenv==1.0.1
```

---

*Desarrollado para el programa ADSO19 — SENA*
