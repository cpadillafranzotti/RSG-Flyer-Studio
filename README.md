# RSG Leadership Flyers

Generador reproducible de flyers de "Leadership team" para los Regional Student Groups (RSG) del ISCB Student Council.
Llenás una planilla (CSV o Google Sheet) con año, RSG, rol, nombre y foto. El script genera **todos los flyers al instante**: uno por RSG × tema × formato, en PNG listo para publicar.

## La forma fácil: Flyer Studio (web)

`web/index.html` es una app web estática que se publica sola en GitHub Pages (`.github/workflows/pages.yml`):

1. Pegás el link del Google Sheet (compartido con *Cualquier persona con el enlace · Lector*).
2. La página lee las pestañas `members` y `rsgs`.
3. Elegís año, RSG, **modelo** (hex / clean / bold) y formato, y ves los flyers en vivo.
4. Descargás cada PNG o todos juntos en un ZIP (2160 px).

Si el sheet no se puede leer, también se puede copiar y pegar cada pestaña. Las fotos pueden ser links de Drive o archivos que se arrastran a la página (se emparejan por nombre de archivo).

Activarlo: **Settings → Pages → Source: GitHub Actions**. La app queda en `https://<usuario>.github.io/<repo>/`.
Los diseños salen de `templates/`: si editás un tema, `web/build.py` lo copia a la app (el workflow lo corre solo).

## La forma por script (lotes / histórico)

```
data/members.csv  ─┐
data/rsgs.csv     ─┼─► generate.py ─► output/<año>/<rsg>_<año>_<tema>_<formato>.png
templates/        ─┘                  output/index.html  (galería para revisar y descargar)
```

## Cambiar de año = agregar filas

No se rediseña nada. Agregás las filas del nuevo año en la hoja `members` y corrés el generador:

```bash
python generate.py                 # último año de la hoja, todos los RSG, los 3 temas, formato cuadrado
python generate.py --year 2027 --rsg argentina,nigeria --format all
python generate.py --year all      # regenera el histórico completo
```

## La planilla (2 pestañas)

### `members` — una fila por persona por año

| year | rsg | order | role | name | photo |
|---|---|---|---|---|---|
| 2026 | nigeria | 1 | President | Ada Okonkwo-Bello | nigeria/ada.jpg |
| 2026 | nigeria | 2 | Secretary | Tunde Adeyemi | https://drive.google.com/file/d/…/view |
| 2026 | nigeria | 3 | Faculty Advisor | Dr. Ngozi Eze | |

- `rsg`: slug corto en minúsculas; tiene que coincidir con la pestaña `rsgs`.
- `order`: orden en el flyer (izquierda→derecha, arriba→abajo).
- `photo` acepta:
  - un archivo en `assets/photos/` (o `assets/photos/<rsg>/`),
  - una URL directa a imagen,
  - un link de Google Drive (el archivo tiene que estar compartido como *"Cualquier persona con el enlace"*).
  - **vacío** → se muestran las iniciales, así podés generar borradores antes de tener las fotos.
- Fotos cuadradas, ≥600 px, cara centrada. Se recortan en círculo automáticamente.

### `rsgs` — una fila por RSG (se completa una sola vez)

| columna | ejemplo | uso |
|---|---|---|
| rsg | `argentina` | slug |
| display_name | `RSG-Argentina` | título grande (si empieza con `RSG-` el prefijo va en color de acento) |
| country | `Argentina` | texto del logo generado |
| website | `rsg-argentina.iscbsc.org` | |
| logo | `argentina.png` | archivo en `assets/logos/`, URL o link de Drive. **Vacío** → genera un logo circular con colores de bandera |
| flag_colors | `#74acdf\|#ffffff\|#74acdf` | 3 colores separados por `\|` para el logo generado y el tema *bold* |
| flag_layout | `horizontal` / `vertical` | orientación de las franjas |
| accent | `#74acdf` | color de acento del RSG |
| handle | `@iscbsc` | redes |
| email | `rsg@iscbsc.org` | contacto |

Plantilla para importar: `data/members.csv` y `data/rsgs.csv` (Google Sheets → Archivo → Importar → Insertar hojas nuevas).

## Conectar un Google Sheet

1. Creá un Sheet con dos pestañas `members` y `rsgs` (mismas columnas).
2. Compartilo como *"Cualquier persona con el enlace puede ver"*.
3. Copiá el link de **cada pestaña** (el link incluye `#gid=…`, que identifica la pestaña).

```bash
python generate.py \
  --members "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=0" \
  --rsgs    "https://docs.google.com/spreadsheets/d/<ID>/edit#gid=123456789"
```

O con variables de entorno: `MEMBERS_SRC` y `RSGS_SRC`.

## Generar desde GitHub, sin instalar nada

El workflow `.github/workflows/flyers.yml`:

1. En el repo: **Settings → Secrets and variables → Actions → Variables** → crear `MEMBERS_SHEET_URL` y `RSGS_SHEET_URL` con los links de las pestañas.
2. **Settings → Pages → Source: GitHub Actions**.
3. **Actions → Generate RSG flyers → Run workflow** (elegís año / RSG / tema / formato).
4. Al terminar, los PNG se bajan como *artifact* del run (GitHub Pages queda para la app web).

También corre solo cada vez que se pushea un cambio en `data/`, `templates/` o `assets/`.

## Temas y formatos

| tema | estilo |
|---|---|
| `hex` | navy oscuro con malla hexagonal, tipografía outline — el más cercano al flyer 2025 original |
| `clean` | fondo claro editorial, anillos con color de acento |
| `bold` | campo de color del RSG con franja de bandera, año gigante |

| formato | tamaño | uso |
|---|---|---|
| `square` | 1080×1080 | post Instagram / LinkedIn |
| `portrait` | 1080×1350 | post Instagram 4:5 |
| `story` | 1080×1920 | stories |

`--scale 2` (default) exporta al doble de resolución (2160 px de ancho).
El layout se adapta automáticamente a equipos de 1 a 8 personas (ver `data/examples/stress_test_members.csv`).

## Logos institucionales del footer

Poné los archivos oficiales en `assets/logos/` con el prefijo `footer_` (por ejemplo `footer_1_iscbsc.png`, `footer_2_iscb.png`); se muestran en orden alfabético. Si no hay ninguno, se muestra el texto "ISCB Student Council".

## Agregar un tema nuevo

1. Copiá `templates/themes/hex.css` → `templates/themes/<nombre>.css` y cambiá los selectores `.theme-hex` por `.theme-<nombre>`.
2. Opcional: `templates/themes/<nombre>_bg.svg` para la decoración de fondo.
3. Ya aparece en `--theme all`. El layout (`templates/base.css`) es compartido, así que el tema solo toca color, tipografía y decoración.

Para debuggear un diseño: `--keep-html` deja los HTML intermedios en `output/_html/` para abrirlos en el navegador.

## Instalación local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
python generate.py
```
