"""
Regenera js/data.js a partir de los reportes del SGA.

Uso:
    python scripts/build_data.py

Requiere: pandas y openpyxl (pip install pandas openpyxl)

FUENTES
-------
1. Reportes del SGA: data/curso_niv_1S2026_sga*.xlsx (o .csv) -- salida de la
   query est_cal_sga_niv_grado.sql. Puede ser un unico archivo con las 38
   carreras o varios archivos parciales: se leen todos los que matcheen el
   patron y cada carrera que aparezca en alguno se toma de ahi. Para
   actualizar datos basta con reemplazar/agregar archivos en data/ y volver a
   correr; no hay que tocar este script.
2. Base (respaldo): data/base_sga_1S2026.js -- snapshot del js/data.js del
   2026-07-30, tambien en git (commit ebe1316). Solo aporta las carreras que
   NO aparezcan en ningun reporte, para no perderlas si alguna vez se corre
   con un export parcial. Con el export completo del 11/08/2026 no aporta
   ninguna fila y el dashboard queda 100% con actas cerradas.

POR QUE SGA Y NO MOODLE (fuente anterior, ver git log de este archivo): las
notas de Moodle quedaron desactualizadas para estudiantes a quienes se les
ayudo a subir la nota despues del examen (ej. cedula 0957410301: Fisica
68->70 y Matematicas 62->70, ambas de REPROBADO a APROBADO). El SGA es el
sistema academico oficial y refleja esos ajustes; Moodle no.

"NO REALIZO EXAMEN": el SGA marcaba con `EN CURSO` al estudiante-curso sin
examen calificado, pero al cerrar el periodo deja como REPROBADO al que no
se presento. O sea que el estado ya no distingue "no rindio" de "rindio y
reprobo". La marca estable es `ex = 0`: se verifico contra el corte del
30/07 que las 32.926 filas calificadas tienen ex > 0 y las 5.731 `EN CURSO`
tienen todas ex = 0, y en el export del 11/08 la nota final maxima entre las
filas con ex = 0 es 40, o sea solo puntos de test. Por eso el tercer estado
del dashboard se reconstruye con `ex == 0 -> No realizo examen`, que es lo
que mantiene vivos el "% Rindio examen" y el "% Aprobado sobre quienes
rindieron". OJO: para el SGA esas matriculas son reprobadas; el dashboard
las cuenta aparte a proposito.

IDENTIDAD DE ESTUDIANTE: se usa `id_estudiante` (no `cedula`) -- no tiene
nulos y es 1-a-1 con la cedula cuando esta existe. OJO: `id_estudiante` es
un ID interno de cada sistema; los valores del SGA NO son los mismos IDs
que traia el CSV de Moodle (numeraciones internas distintas) - para cruzar
ambas fuentes hay que usar `cedula`.

El base ya perdio los IDs (guarda indices anonimos), asi que cuando aporta
filas se reidentifica al estudiante entre base y reporte por su firma: el
conjunto de (carrera, asignatura, docente, promedio de test) de sus filas.
Los test son previos al examen, o sea que no cambian entre cortes.
"""
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE = DATA / "base_sga_1S2026.js"
SRC_GLOB = "curso_niv_1S2026_sga*"          # .xlsx o .csv
SRC_SUFFIXES = {".xlsx", ".xls", ".csv"}
OUT = ROOT / "js" / "data.js"

# Fecha del reporte del que sale cada carrera; queda en meta.fuentes de
# js/data.js solo como trazabilidad (el dashboard no la muestra).
CORTE_BASE = "2026-07-30"
CORTE_NUEVO = "2026-08-11"

LOWER_WORDS = {"de", "del", "la", "las", "el", "los", "y", "en", "a", "al", "con", "por", "para"}

# El CSV fuente trae tildes inconsistentes/perdidas en "carrera" y "asignatura"
# (p.ej. "ADMINISTRACION", "FISICA" sin tilde). Se corrige con la ortografia
# oficial tal como aparece en el Informe Tecnico ITI-DIPA-NVERAV-2026-004,
# para que las etiquetas del dashboard sean presentables. La clave es la
# version sin tildes en mayusculas (norm_key) para que el match sea robusto
# sin importar como haya llegado la tilde en el CSV.
_REPORT_CARRERAS = [
    "Licenciatura en Fisioterapia", "Licenciatura en Nutrición y Dietética",
    "Licenciatura en Enfermería", "Ingeniería Ambiental",
    "Licenciatura en Pedagogía de la Actividad Física y Deporte", "Ingeniería Industrial",
    "Tecnologías de la Información en Línea", "Ingeniería Civil", "Software",
    "Ingeniería en Software", "Ingeniería en Alimentos", "Educación",
    "Licenciatura en Turismo", "Psicología Clínica", "Educación Inicial en Línea",
    "Trabajo Social", "Licenciatura en Educación Inicial", "Administración de Empresas",
    "Licenciatura en Contabilidad y Auditoría", "Economía en Línea", "Trabajo Social en Línea",
    "Ingeniería en Biotecnología", "Educación Especial", "Turismo en Línea",
    "Pedagogía de las Ciencias Experimentales", "Agronegocios", "Arquitectura Sostenible",
    "Economía", "Administración de Empresas en Línea",
    "Pedagogía de los Idiomas Nacionales y Extranjeros en Línea",
    "Pedagogía de la Lengua y la Literatura", "Educación Básica en Línea", "Derecho en Línea",
    "Licenciatura en Pedagogía de los Idiomas Nacionales y Extranjeros",
    "Licenciatura en Comunicación", "Multimedia y Producción Audiovisual",
    "Comunicación en Línea", "Medicina",
]
_REPORT_ASIGNATURAS = [
    "Anatomía", "Física", "Neuroanatomía", "Matemáticas", "Química",
    "Introducción a la Pedagogía de la Actividad Física y Deporte",
    "Fisiología del Sistema Nervioso", "Biología", "Introducción a la Contabilidad",
    "Teoría de la Arquitectura Sostenible", "Introducción a la Educación Inicial",
    "Introducción a la Pedagogía de las Ciencias Experimentales", "Sociedad y Cultura",
    "Inglés", "Epistemología del Turismo", "Pensamiento Computacional",
    "Fundamentos del Análisis Económico", "Derecho Romano",
    "Prototipado Visual y Composición", "Comunicación y Lenguaje Académico",
    "Fundamentos de la Comunicación Digital", "Introducción a la Educación Especial",
    "Introducción a la Educación Básica", "Introducción a la Administración",
    "Lenguaje, Lectura Crítica y Escritura Académica",
    "Arquitectura de Contenidos y Narrativa Transmedia", "Bioquímica",
]


def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm_key(s):
    """Clave de normalizacion para deduplicar variantes con/sin tilde."""
    return " ".join(strip_accents(str(s)).upper().split())


def title_es(s):
    s = " ".join(str(s).split())
    out = []
    for i, w in enumerate(s.split(" ")):
        wl = w.lower()
        if i > 0 and wl in LOWER_WORDS:
            out.append(wl)
        else:
            # capitaliza preservando tildes/enies (str.capitalize funciona bien con unicode)
            out.append(wl.capitalize())
    return " ".join(out)


CARRERA_FIX = {norm_key(name): name for name in _REPORT_CARRERAS}
ASIGNATURA_FIX = {norm_key(name): name for name in _REPORT_ASIGNATURAS}


def carrera_label(raw):
    """'Nivelacion Licenciatura en Fisioterapia' (texto original, con tildes
    inconsistentes) -> 'Licenciatura en Fisioterapia' (ortografia oficial del
    informe si esta en CARRERA_FIX; si no, mejor esfuerzo sobre el texto crudo)."""
    upper_noaccent = strip_accents(str(raw)).upper()
    if upper_noaccent.startswith("NIVELACION "):
        raw = str(raw)[len("NIVELACION "):]
        upper_noaccent = upper_noaccent[len("NIVELACION "):]
    fixed = CARRERA_FIX.get(" ".join(upper_noaccent.split()))
    return fixed if fixed else title_es(raw)


def asignatura_label(raw):
    fixed = ASIGNATURA_FIX.get(norm_key(raw))
    return fixed if fixed else title_es(raw)


def docente_label(raw):
    return title_es(raw)


def modalidad_label(raw):
    m = norm_key(raw)
    if m == "EN LINEA":
        return "En línea"
    if m == "SEMIPRESENCIAL":
        return "Semipresencial"
    return "Presencial"


AREA_RULES = [
    (["ENFERMERIA", "FISIOTERAPIA", "NUTRICION", "MEDICINA", "PSICOLOGIA CLINICA"], "Salud y Servicios Sociales"),
    (["TRABAJO SOCIAL"], "Ciencias Sociales y Trabajo Social"),
    (["EDUCACION", "PEDAGOGIA"], "Educacion y Pedagogia"),
    (["INGENIERIA", "SOFTWARE", "TECNOLOGIAS DE LA INFORMACION", "ARQUITECTURA"], "Ingenieria y Tecnologia"),
    (["ADMINISTRACION", "CONTABILIDAD", "ECONOMIA", "AGRONEGOCIOS"], "Administrativas, Economicas y Agropecuarias"),
    (["COMUNICACION", "MULTIMEDIA"], "Comunicacion y Arte"),
    (["DERECHO"], "Juridica"),
    (["TURISMO"], "Turismo"),
]


def area_for(norm_carrera):
    for keywords, area in AREA_RULES:
        if any(k in norm_carrera for k in keywords):
            return area
    return "Otras"


def r1(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    return round(float(x) + 1e-9, 1)


# Estados del dashboard (el indice se guarda en cada fila)
ESTADO_LABELS = ["Aprobado", "Reprobado", "No realizó examen"]
AP, REP, NORINDIO = 0, 1, 2


def load_js_data(path):
    """Lee un archivo 'const DATA = {...};' y devuelve el dict."""
    txt = path.read_text(encoding="utf-8")
    start = txt.index("{")
    end = txt.rstrip().rstrip(";").rindex("}") + 1
    return json.loads(txt[start:end])


def read_source(path):
    """Lee un reporte del SGA, sea Excel o CSV."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, encoding="utf-8-sig")
    return pd.read_excel(path, sheet_name=0)


EMPTY_BASE = {
    "dict": {"carrera": [], "carreraModalidad": [], "asignatura": [], "docente": [],
             "estado": ESTADO_LABELS},
    "rows": [],
}


def load_base():
    """Respaldo opcional: solo aporta carreras ausentes de los reportes.

    Con un export completo del SGA no hace falta, asi que si no esta se sigue
    igual (para recuperarlo: git show ebe1316:js/data.js > data/base_sga_1S2026.js).
    """
    if not BASE.exists():
        return EMPTY_BASE
    return load_js_data(BASE)


class Registry:
    """Diccionario incremental clave-normalizada -> etiqueta presentable."""

    def __init__(self):
        self.label = {}

    def add(self, key, label):
        self.label.setdefault(key, label)
        return key


def main():
    base = load_base()
    sources = sorted(p for p in DATA.glob(SRC_GLOB)
                     if p.suffix.lower() in SRC_SUFFIXES and not p.name.startswith("~$"))
    if not sources:
        raise SystemExit(f"No hay reportes del SGA ({DATA}/{SRC_GLOB} con extension {sorted(SRC_SUFFIXES)})")

    # ---------- 1. reportes del SGA ----------
    frames = []
    for path in sources:
        df = read_source(path)
        df["_archivo"] = path.name
        frames.append(df)
    new = pd.concat(frames, ignore_index=True)

    new["ck"] = new["carrera"].map(lambda s: norm_key(carrera_label(s)))
    new["ak"] = new["asignatura"].map(lambda s: norm_key(asignatura_label(s)))
    new["dk"] = new["docente"].map(norm_key)

    dup = new.duplicated(subset=["id_estudiante", "ck", "ak"]).sum()
    if dup:
        print(f"AVISO: {dup} filas duplicadas (mismo estudiante+carrera+asignatura) entre los CSV")

    covered = set(new["ck"])

    # ---------- 2. diccionarios ----------
    carreras, asignaturas, docentes = Registry(), Registry(), Registry()
    modalidad, fuente = {}, {}

    for i, label in enumerate(base["dict"]["carrera"]):
        k = norm_key(label)
        carreras.add(k, label)
        modalidad[k] = base["dict"]["carreraModalidad"][i]
        fuente[k] = 0
    for label in base["dict"]["asignatura"]:
        asignaturas.add(norm_key(label), label)
    for label in base["dict"]["docente"]:
        docentes.add(norm_key(label), label)

    for t in new.itertuples(index=False):
        carreras.add(t.ck, carrera_label(t.carrera))
        asignaturas.add(t.ak, asignatura_label(t.asignatura))
        docentes.add(t.dk, docente_label(t.docente))
        modalidad[t.ck] = modalidad_label(t.modalidad)
        fuente[t.ck] = 1

    carrera_keys = sorted(carreras.label)
    asignatura_keys = sorted(asignaturas.label)
    docente_keys = sorted(docentes.label)
    c_idx = {k: i for i, k in enumerate(carrera_keys)}
    a_idx = {k: i for i, k in enumerate(asignatura_keys)}
    d_idx = {k: i for i, k in enumerate(docente_keys)}

    # ---------- 3. filas del base que se conservan / firmas de las que se reemplazan ----------
    b_car = base["dict"]["carrera"]
    b_asig = base["dict"]["asignatura"]
    b_doc = base["dict"]["docente"]
    b_est = base["dict"]["estado"]
    b_est_idx = {lab: ESTADO_LABELS.index(lab) for lab in b_est}

    kept = []                      # filas de carreras no actualizadas (ya con indices nuevos)
    base_rows_covered = defaultdict(list)   # sid del base -> filas (para la firma)
    for r in base["rows"]:
        ck = norm_key(b_car[r[1]])
        row = [r[0], c_idx[ck], a_idx[norm_key(b_asig[r[2]])], d_idx[norm_key(b_doc[r[3]])],
               b_est_idx[b_est[r[4]]], r[5], r[6], r[7]]
        if ck in covered:
            base_rows_covered[r[0]].append((ck, norm_key(b_asig[r[2]]), norm_key(b_doc[r[3]]), r[6]))
        else:
            kept.append(row)

    # ---------- 4. reidentificacion de estudiantes base <-> CSV ----------
    new_rows_by_id = defaultdict(list)
    for t in new.itertuples(index=False):
        new_rows_by_id[t.id_estudiante].append((t.ck, t.ak, t.dk, r1((t.n1 + t.n2 + t.n3 + t.n4) / 4.0)))

    def by_signature(d):
        out = defaultdict(list)
        for sid, rows in d.items():
            out[tuple(sorted(rows))].append(sid)
        return out

    sig_base = by_signature(base_rows_covered)
    sig_new = by_signature(new_rows_by_id)
    id_to_sid = {}
    for sig, new_ids in sig_new.items():
        base_sids = sig_base.get(sig, [])
        # dentro de una misma firma los estudiantes son indistinguibles en las
        # carreras actualizadas: se emparejan en orden, de forma determinista
        for nid, bsid in zip(sorted(new_ids), sorted(base_sids)):
            id_to_sid[nid] = bsid
    sin_match = len(new_rows_by_id) - len(id_to_sid)

    next_sid = max((r[0] for r in base["rows"]), default=-1) + 1
    for nid in sorted(new_rows_by_id):
        if nid not in id_to_sid:
            id_to_sid[nid] = next_sid
            next_sid += 1

    # ---------- 5. filas nuevas ----------
    fresh = []
    no_rindio = Counter()
    for t in new.itertuples(index=False):
        est_raw = norm_key(t.estado_materia)
        if t.ex == 0:
            # No se presento al examen: el SGA lo deja como REPROBADO al cerrar el
            # periodo (y como EN CURSO si todavia no lo cerro). El dashboard lo
            # separa en su propio estado -- ver docstring.
            estado = NORINDIO
            no_rindio[est_raw] += 1
        elif est_raw == "EN CURSO":
            raise SystemExit(f"Fila EN CURSO con ex={t.ex} (se esperaba ex=0): {t.carrera} / {t.asignatura}")
        else:
            estado = AP if est_raw == "APROBADO" else REP
        fresh.append([
            id_to_sid[t.id_estudiante], c_idx[t.ck], a_idx[t.ak], d_idx[t.dk], estado,
            r1(t.nota_final), r1((t.n1 + t.n2 + t.n3 + t.n4) / 4.0), r1(t.ex),
        ])

    # ---------- 6. compactar indices de estudiante ----------
    rows = kept + fresh
    remap = {}
    for r in rows:
        if r[0] not in remap:
            remap[r[0]] = len(remap)
        r[0] = remap[r[0]]

    # Trazabilidad de que reporte del SGA salio cada carrera. No se muestra en el
    # dashboard: sirve para saber que hay que reexportar cuando se quiera
    # refrescar una carrera. Si el base no aporto ninguna carrera queda una sola
    # fuente, o sea que todo el dashboard salio del mismo reporte.
    FUENTES_POSIBLES = [
        {"fecha": CORTE_BASE, "etiqueta": "Reporte SGA del 30/07/2026"},
        {"fecha": CORTE_NUEVO, "etiqueta": "Reporte SGA del 11/08/2026",
         "archivos": [p.name for p in sources]},
    ]
    usadas = sorted({fuente[k] for k in carrera_keys})
    fmap = {f: i for i, f in enumerate(usadas)}
    fuentes = [FUENTES_POSIBLES[f] for f in usadas]
    carrera_fuente = [fmap[fuente[k]] for k in carrera_keys]

    data = {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "totalRows": len(rows),
            "totalStudents": len(remap),
            "fuentes": fuentes,
            "carrerasPorFuente": [carrera_fuente.count(i) for i in range(len(fuentes))],
        },
        "dict": {
            "carrera": [carreras.label[k] for k in carrera_keys],
            "carreraModalidad": [modalidad[k] for k in carrera_keys],
            "carreraArea": [area_for(k) for k in carrera_keys],
            "carreraFuente": carrera_fuente,
            "asignatura": [asignaturas.label[k] for k in asignatura_keys],
            "docente": [docentes.label[k] for k in docente_keys],
            "estado": ESTADO_LABELS,
        },
        # fila: [studentIdx, carreraIdx, asignaturaIdx, docenteIdx, estadoIdx, notaFinal, testProm, examenFinal]
        "rows": rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # ---------- 7. resumen ----------
    print(f"Escrito {OUT}")
    print(f"  reportes: {', '.join(p.name for p in sources)}")
    print(f"  {len(rows)} filas estudiante-curso ({len(fresh)} de los reportes, {len(kept)} del base), "
          f"{len(remap)} estudiantes")
    print(f"  {len(carrera_keys)} carreras, {len(asignatura_keys)} asignaturas, {len(docente_keys)} docentes")
    if len(kept):
        faltan = [carreras.label[k] for k in carrera_keys if fuente[k] == 0]
        print(f"  AVISO: {len(faltan)} carreras no vienen en los reportes y se toman del base "
              f"({CORTE_BASE}): {', '.join(faltan)}")
        print(f"  reidentificados por firma: {len(new_rows_by_id) - sin_match}/{len(new_rows_by_id)} estudiantes"
              f"{'' if not sin_match else f' ({sin_match} sin match, cuentan como nuevos)'}")
    else:
        print(f"  todas las carreras salen de los reportes del {CORTE_NUEVO} (el base no aporta filas)")
    detalle = ", ".join(f"{n} venian como {e}" for e, n in no_rindio.most_common())
    print(f"  filas con ex=0 contadas como 'No realizó examen': {sum(no_rindio.values())} ({detalle})")
    est_count = Counter(r[4] for r in rows)
    for i, lab in enumerate(ESTADO_LABELS):
        print(f"    {lab}: {est_count[i]} ({est_count[i] / len(rows) * 100:.2f}%)")


if __name__ == "__main__":
    main()
