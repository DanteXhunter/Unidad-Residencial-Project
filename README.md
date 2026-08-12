# Residencial Admin

Aplicación web para la administración de unidades residenciales (condominios y
fraccionamientos). Proyecto escolar de la materia de Reingeniería.

Permite a un administrador iniciar sesión y gestionar unidades, residentes,
pagos, incidencias, avisos y usuarios del sistema, con un panel de indicadores
alimentado por consultas reales a la base de datos.

---

## 1. Tecnologías

| Capa               | Herramienta                                             |
| ------------------ | ------------------------------------------------------- |
| Lenguaje           | Python 3.12                                             |
| Framework web      | FastAPI + Uvicorn                                       |
| ORM                | SQLAlchemy 2.0 (estilo tipado con `Mapped`)             |
| Migraciones        | Alembic                                                 |
| Base de datos      | PostgreSQL (local o Supabase)                           |
| Driver             | psycopg 3                                               |
| Plantillas         | Jinja2 (renderizado en el servidor)                     |
| Estilos            | Tailwind CSS v4 (compilado, sin CDN)                    |
| Interactividad     | htmx + ~90 líneas de JavaScript propio                  |
| Contraseñas        | Argon2id (`argon2-cffi`)                                |
| Sesiones           | Cookie firmada (`SessionMiddleware` de Starlette)       |

No se usa React ni ningún framework de frontend: **todo el código es Python**,
salvo el JavaScript mínimo para abrir modales y el menú lateral.

### Por qué no se usa Supabase Auth

Supabase aporta aquí únicamente **PostgreSQL**. La autenticación está
implementada en Python contra la tabla `users`. Esto evita dos problemas
habituales al mezclar Supabase Auth con un backend propio:

- La tabla de perfiles tendría que apuntar a `auth.users`, y entonces **no se
  podrían sembrar usuarios de prueba** sin crear antes cuentas reales.
- Las políticas RLS que consultan el rol dentro de la propia tabla de perfiles
  provocan **recursión infinita** y rompen la aplicación en tiempo de ejecución.

Como la app se conecta con el usuario dueño de la base, **no se necesita RLS**:
el único camino hacia los datos pasa por el servidor, que ya exige sesión válida
en todas las rutas.

---

## 2. Requisitos previos

- **Python 3.12 o superior**
- **PostgreSQL 14+**, ya sea local o un proyecto de Supabase
- Node.js *solo* si vas a modificar los estilos (el CSS compilado ya está en el
  repositorio, así que para ejecutar la app **no hace falta**)

---

## 3. Instalación

```bash
git clone <url-del-repositorio>
cd Unidad-Residencial-Project

python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

---

## 4. Variables de entorno

```bash
cp .env.example .env
```

Edita `.env`:

| Variable          | Descripción                                                    |
| ----------------- | -------------------------------------------------------------- |
| `DATABASE_URL`    | Cadena de conexión a PostgreSQL.                                |
| `SECRET_KEY`      | Llave para firmar la cookie de sesión. **Genera una propia.**   |
| `SESSION_MAX_AGE` | Duración de la sesión en segundos (28800 = 8 horas).            |
| `COOKIE_SECURE`   | `true` al desplegar con HTTPS; `false` en desarrollo local.     |

Genera una llave nueva con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

> `.env` está en `.gitignore`: nunca subas credenciales al repositorio.

---

## 5. Configurar la base de datos

### Opción A · PostgreSQL local

```bash
createdb residencial_dev
```

```env
DATABASE_URL=postgresql+psycopg://localhost:5432/residencial_dev
```

### Opción B · Supabase

1. Entra a [supabase.com](https://supabase.com) y crea un proyecto.
2. Ve a **Project Settings → Database → Connection string**.
3. Copia la cadena del **Session pooler** (puerto **5432**).
4. Sustituye `[YOUR-PASSWORD]` por la contraseña de la base de datos.
5. Pégala en `.env` anteponiendo el driver `+psycopg`:

```env
DATABASE_URL=postgresql+psycopg://postgres.abcdefgh:TU_PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
```

**Usa el puerto 5432 (Session pooler), no el 6543.** El *transaction pooler*
del puerto 6543 no admite sentencias preparadas y Alembic falla al migrar. La
aplicación las desactiva sola si detecta ese puerto, pero las migraciones deben
correrse contra el 5432.

No hay que ejecutar ningún `schema.sql` a mano: el esquema se crea con Alembic
en el siguiente paso.

---

## 6. Crear las tablas

```bash
alembic upgrade head
```

Esto crea las **6 tablas** del sistema con sus llaves foráneas, índices y
restricciones. Para revertir todo: `alembic downgrade base`.

---

## 7. Cargar datos de demostración

```bash
python -m scripts.seed
```

Genera 16 unidades, 12 residentes, 42 pagos repartidos en cuatro meses, 8
incidencias y 5 avisos, para que el panel no se vea vacío en la revisión.
Usa `--reset` para borrar lo existente y volver a generarlo.

El seed crea esta cuenta de demostración:

```
Correo:     admin@residencial.mx
Contraseña: Admin1234
```

> Es una credencial de práctica generada en tu equipo. **Cámbiala** antes de
> exponer la aplicación fuera de tu máquina.

### Crear un administrador propio

```bash
python -m scripts.create_admin
```

Pide correo, nombre y contraseña (que no se muestra al escribirla).

---

## 8. Ejecutar la aplicación

```bash
uvicorn app.main:app --reload
```

Abre <http://127.0.0.1:8000>. Serás redirigido a `/login`.

---

## 9. Estructura del proyecto

```
app/
├── main.py              Punto de entrada, middleware y manejo de errores
├── config.py            Configuración leída del .env
├── database.py          Motor de SQLAlchemy y sesión por request
├── dependencies.py      Usuario en sesión y protección de rutas
├── security.py          Hash y verificación de contraseñas (Argon2)
├── flash.py             Mensajes de éxito/error entre peticiones
├── templating.py        Jinja2: filtros, globales y helper render()
├── models/              Las 6 tablas como clases de SQLAlchemy
├── schemas/             Validación de formularios con Pydantic
├── services/            Lógica de negocio (no vive en los routers)
├── routers/             Una pantalla del panel por módulo
├── templates/           Plantillas Jinja2
└── static/              CSS compilado, htmx y JavaScript propio

migrations/              Migraciones de Alembic
scripts/                 seed.py y create_admin.py
```

---

## 10. Modelo de datos

Seis tablas relacionadas:

```
users ──────< announcements        (author_id, ON DELETE SET NULL)

units ──────< residents            (unit_id,   ON DELETE RESTRICT)
      ──────< payments             (unit_id,   ON DELETE RESTRICT)
      ──────< incidents            (unit_id,   ON DELETE RESTRICT)

residents ──< payments             (resident_id, ON DELETE RESTRICT)
```

| Tabla           | Contenido                                                     |
| --------------- | ------------------------------------------------------------- |
| `users`         | Cuentas con acceso al panel. Contraseña en hash Argon2.       |
| `units`         | Casas y departamentos. `unit_number` es **único**.            |
| `residents`     | Propietarios e inquilinos, ligados a una unidad.              |
| `payments`      | Cuotas y cargos, con mes/año numéricos para poder filtrar.    |
| `incidents`     | Reportes de mantenimiento (la unidad es opcional: áreas comunes). |
| `announcements` | Avisos en borrador o publicados.                              |

Decisiones que conviene conocer:

- **`ON DELETE RESTRICT`, no `CASCADE`.** Borrar una unidad con residentes o
  pagos no destruye su historial: la aplicación lo impide y explica por qué.
- **El mes se guarda como entero**, no como texto, para poder ordenar y filtrar
  cronológicamente. La etiqueta en español se genera al mostrarlo.
- **Los catálogos son `VARCHAR` con `CHECK`**, no tipos `ENUM` nativos, porque
  añadir un valor nuevo a un `ENUM` de Postgres exige un `ALTER TYPE`.
- **`updated_at` se actualiza solo** en cada modificación.

---

## 11. Rutas

| Ruta                | Descripción                                 |
| ------------------- | ------------------------------------------- |
| `/login`            | Inicio de sesión (única ruta pública)       |
| `/dashboard`        | Indicadores y gráficas                      |
| `/units`            | CRUD de unidades                            |
| `/residents`        | CRUD de residentes                          |
| `/payments`         | CRUD de pagos + acción "Marcar pagado"      |
| `/incidents`        | CRUD de incidencias + cambio rápido de estado |
| `/announcements`    | CRUD de avisos                              |
| `/users`            | CRUD de usuarios del sistema                |

Todas menos `/login` exigen sesión activa; sin ella redirigen al login.
Cualquier ruta desconocida muestra una página 404 con el diseño de la app.

---

## 12. Flujo de demostración

1. Abrir <http://127.0.0.1:8000> → redirige a `/login`.
2. Entrar con `admin@residencial.mx` / `Admin1234`.
3. Revisar los indicadores del **Dashboard**.
4. **Unidades** → *Nueva unidad* → crearla → editarla.
5. Intentar crear otra con el mismo número → se rechaza por duplicado.
6. **Residentes** → agregar un residente a esa unidad.
7. **Pagos** → registrar un pago pendiente → *Marcar pagado*.
8. Volver al **Dashboard**: los indicadores y la gráfica ya reflejan el cambio.
9. **Incidencias** → crear una → *Iniciar* → *Resolver*.
10. **Avisos** → crear uno como *Publicado* (guarda la fecha automáticamente).
11. **Unidades** → intentar eliminar la unidad que tiene residentes y pagos:
    la app lo impide y explica el motivo.
12. Eliminar en orden: pago → incidencia → residente → unidad.
13. **Cerrar sesión** y comprobar que `/dashboard` vuelve a pedir login.

---

## 13. Modificar los estilos

El CSS compilado (`app/static/css/app.css`) **ya está versionado**, así que la
app funciona sin Node. Solo si vas a cambiar el diseño:

```bash
npm install
npm run build:css     # compila una vez
npm run watch:css     # recompila al guardar
```

Las clases se definen en `app/static/css/input.css`.

---

## 14. Estado del proyecto

Verificado de extremo a extremo contra PostgreSQL con 58 comprobaciones
automatizadas: protección de rutas, login correcto e incorrecto, los cuatro
verbos CRUD de cada módulo, validaciones, restricciones de integridad, páginas
404 y cierre de sesión.

**Pendientes conocidos**, fuera del alcance de la entrega:

- No hay paginación en las tablas (con cientos de registros convendría añadirla).
- El estado *Vencido* de un pago se asigna manualmente; no hay un proceso que lo
  calcule al pasar la fecha límite.
- Los roles `Administrador` y `Operador` existen en la base de datos, pero
  todavía no restringen acciones distintas dentro del panel.
