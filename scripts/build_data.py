"""
Regenera js/data.js a partir de los reportes del SGA.

Uso:
    python scripts/build_data.py

Requiere: pandas y openpyxl (pip install pandas openpyxl)

FUENTE
------
data/curso_niv_1S2026_sga*.csv (o .xlsx) -- salida de la query
est_cal_sga_niv_grado.sql. Se leen todos los archivos que matcheen el patron
y tengan las columnas de REQUIRED; los que no las tengan (exports viejos sin
inscripcion_id) se ignoran con un aviso, para que un archivo olvidado en
data/ no duplique filas. Si falta alguna de las 38 carreras del informe
tambien se avisa por consola. Para actualizar datos basta con reemplazar el
archivo en data/ y volver a correr; no hay que tocar este script.

POR QUE SGA Y NO MOODLE (fuente anterior, ver git log de este archivo): las
notas de Moodle quedaron desactualizadas para estudiantes a quienes se les
ayudo a subir la nota despues del examen (ej. cedula 0957410301: Fisica
68->70 y Matematicas 62->70, ambas de REPROBADO a APROBADO). El SGA es el
sistema academico oficial y refleja esos ajustes; Moodle no.

ESTADOS: se toman los del SGA tal cual (APROBADO / REPROBADO / EN CURSO) y
los porcentajes del dashboard son sobre el total, no sobre un subconjunto:
58,03% / 41,90% / 0,07% en el corte del 11/08/2026.

`EN CURSO` con el periodo cerrado ya no significa "examen sin calificar del
estudiante" sino que el DOCENTE no cerro las calificaciones de esa materia.
Por eso se muestra como tercer estado en vez de fundirlo con reprobado: el
dashboard tiene una tarjeta que nombra al docente, la asignatura y la
carrera donde falta cerrar. Hoy son 27 filas, todas de Pensamiento
Computacional en Administracion de Empresas.

Al que no se presento al examen el SGA lo reprueba, y el dashboard respeta
eso: NO se lo reclasifica. La marca de no haberse presentado es `ex = 0`
(verificado contra el corte del 30/07: las 32.926 filas calificadas tienen
ex > 0 y las 5.731 `EN CURSO` tienen todas ex = 0; y entre las filas con
ex = 0 la nota final maxima es 40, o sea solo puntos de test). Como `ex`
viaja en cada fila, el "% Rindio examen" de la vista Por Carrera se calcula
en el navegador con `ex > 0`, sin necesidad de un estado aparte.

IDENTIDAD: se agrupa por `inscripcion_id` (la matricula de una persona en
una carrera), NO por `id_estudiante` (la persona) ni por `cedula`. Una misma
persona puede estar inscrita en dos carreras a la vez y cursar la misma
asignatura en ambas: en el corte del 11/08/2026 son 12 personas / 13.136
inscripciones, con 22 filas que se pisarian entre si. Agrupar por persona
las fusionaba, subcontaba estudiantes y podia arruinar "aprobados
completamente" (aprobar todo en una carrera y no en la otra). Cada
inscripcion pertenece a una sola carrera, asi que es la unidad correcta para
todo lo que el dashboard llama "estudiante".

`id_estudiante` se sigue leyendo, pero solo para reportar cuantas personas
hay detras de las inscripciones (meta.totalPersonas). OJO: es un ID interno
de cada sistema; los valores del SGA NO son los mismos que traia el CSV de
Moodle - para cruzar ambas fuentes hay que usar `cedula`.
"""
import json
import unicodedata
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SRC_GLOB = "curso_niv_1S2026_sga*"          # .xlsx o .csv
SRC_SUFFIXES = {".xlsx", ".xls", ".csv"}
OUT = ROOT / "js" / "data.js"

# Fecha del reporte; queda en meta.corte de js/data.js como trazabilidad
# (el dashboard no la muestra).
CORTE = "2026-08-12"

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


# Estados del dashboard: son los del SGA tal cual (el indice se guarda en cada
# fila). "En curso" = el docente todavia no cerro las calificaciones de esa
# materia; el dashboard lo muestra aparte justamente para saber a quien reclamar.
ESTADO_LABELS = ["Aprobado", "Reprobado", "En curso"]
ESTADO_IDX = {"APROBADO": 0, "REPROBADO": 1, "EN CURSO": 2}

# numero_matricula = cuantas veces lleva tomada esa asignatura (1ra, 2da, 3ra).
# De 3 en adelante son 9 filas en total, asi que se agrupan en un solo tramo.
MATRICULA_LABELS = ["1ra matrícula", "2da matrícula", "3ra matrícula o más"]


def matricula_idx(n):
    return min(max(int(n), 1), len(MATRICULA_LABELS)) - 1


# Los reportes cambian de nombre de columna segun la version de la query.
COLUMN_ALIASES = {"carrera_estudiante": "carrera", "carrera_asignatura": "carrera"}
REQUIRED = ["inscripcion_id", "carrera", "modalidad", "asignatura", "docente", "numero_matricula",
            "n1", "n2", "n3", "n4", "ex", "nota_final", "estado_materia"]


def read_source(path):
    """Lee un reporte del SGA (Excel o CSV) y normaliza los nombres de columna."""
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, encoding="utf-8-sig")
    else:
        df = pd.read_excel(path, sheet_name=0)
    return df.rename(columns={c: COLUMN_ALIASES.get(c, c) for c in df.columns})


class Registry:
    """Diccionario incremental clave-normalizada -> etiqueta presentable."""

    def __init__(self):
        self.label = {}

    def add(self, key, label):
        self.label.setdefault(key, label)
        return key


def main():
    candidatos = sorted(p for p in DATA.glob(SRC_GLOB)
                        if p.suffix.lower() in SRC_SUFFIXES and not p.name.startswith("~$"))
    if not candidatos:
        raise SystemExit(f"No hay reportes del SGA ({DATA}/{SRC_GLOB} con extension {sorted(SRC_SUFFIXES)})")

    # ---------- 1. reportes del SGA ----------
    frames, sources, ignorados = [], [], []
    for path in candidatos:
        df = read_source(path)
        faltan = [c for c in REQUIRED if c not in df.columns]
        if faltan:
            # p.ej. los exports viejos sin inscripcion_id: se ignoran en vez de
            # duplicar filas o romper el build
            ignorados.append((path.name, faltan))
            continue
        df["_archivo"] = path.name
        # id_estudiante es opcional: solo se usa para reportar cuantas personas
        # hay detras de las inscripciones
        cols = REQUIRED + ["_archivo"] + [c for c in ("id_estudiante",) if c in df.columns]
        frames.append(df[cols])
        sources.append(path)
    for nombre, faltan in ignorados:
        print(f"AVISO: se ignora {nombre}, le faltan columnas: {', '.join(faltan)}")
    if not frames:
        raise SystemExit("Ningun reporte tiene las columnas necesarias (falta reexportar con inscripcion_id)")
    new = pd.concat(frames, ignore_index=True)

    new["ck"] = new["carrera"].map(lambda s: norm_key(carrera_label(s)))
    new["ak"] = new["asignatura"].map(lambda s: norm_key(asignatura_label(s)))
    new["dk"] = new["docente"].map(norm_key)

    dup = new.duplicated(subset=["inscripcion_id", "ak"]).sum()
    if dup:
        print(f"AVISO: {dup} filas duplicadas (misma inscripcion + asignatura) entre los reportes")

    # ---------- 2. diccionarios ----------
    carreras, asignaturas, docentes = Registry(), Registry(), Registry()
    modalidad = {}
    for t in new.itertuples(index=False):
        carreras.add(t.ck, carrera_label(t.carrera))
        asignaturas.add(t.ak, asignatura_label(t.asignatura))
        docentes.add(t.dk, docente_label(t.docente))
        modalidad[t.ck] = modalidad_label(t.modalidad)

    faltantes = [c for c in _REPORT_CARRERAS if norm_key(c) not in carreras.label]
    if faltantes:
        print(f"AVISO: {len(faltantes)} carreras del informe no aparecen en los reportes: "
              f"{', '.join(faltantes)}")

    carrera_keys = sorted(carreras.label)
    asignatura_keys = sorted(asignaturas.label)
    docente_keys = sorted(docentes.label)
    c_idx = {k: i for i, k in enumerate(carrera_keys)}
    a_idx = {k: i for i, k in enumerate(asignatura_keys)}
    d_idx = {k: i for i, k in enumerate(docente_keys)}

    # ---------- 3. identidad: la inscripcion, no la persona ----------
    # Una misma persona puede tener dos inscripciones (dos carreras) y cursar la
    # misma asignatura en ambas; agrupar por persona las fusionaria. Ver docstring.
    ins_idx = {}
    for ins in new["inscripcion_id"]:
        if ins not in ins_idx:
            ins_idx[ins] = len(ins_idx)
    personas = new["id_estudiante"].nunique() if "id_estudiante" in new.columns else None

    # ---------- 4. filas ----------
    rows = []
    sin_examen = 0
    for t in new.itertuples(index=False):
        est_raw = norm_key(t.estado_materia)
        if est_raw not in ESTADO_IDX:
            raise SystemExit(f"estado_materia desconocido: '{t.estado_materia}' en {t.carrera} / {t.asignatura}")
        estado = ESTADO_IDX[est_raw]
        # ex = 0 significa que no se presento al examen final; no cambia el estado
        # (el SGA ya lo reprobo), pero el dashboard lo usa para el "% rindio"
        if t.ex == 0:
            sin_examen += 1
        rows.append([
            ins_idx[t.inscripcion_id], c_idx[t.ck], a_idx[t.ak], d_idx[t.dk], estado,
            r1(t.nota_final), r1((t.n1 + t.n2 + t.n3 + t.n4) / 4.0), r1(t.ex),
            matricula_idx(t.numero_matricula),
        ])

    data = {
        "meta": {
            "generated": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "corte": CORTE,
            "archivos": [p.name for p in sources],
            "totalRows": len(rows),
            "totalStudents": len(ins_idx),   # inscripciones (estudiante-carrera)
            "totalPersonas": personas,       # personas distintas detras de esas inscripciones
        },
        "dict": {
            "carrera": [carreras.label[k] for k in carrera_keys],
            "carreraModalidad": [modalidad[k] for k in carrera_keys],
            "carreraArea": [area_for(k) for k in carrera_keys],
            "asignatura": [asignaturas.label[k] for k in asignatura_keys],
            "docente": [docentes.label[k] for k in docente_keys],
            "estado": ESTADO_LABELS,
            "matricula": MATRICULA_LABELS,
        },
        # fila: [inscripcionIdx, carreraIdx, asignaturaIdx, docenteIdx, estadoIdx, notaFinal,
        #        testProm, examenFinal, matriculaIdx]
        "rows": rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    # ---------- 5. resumen ----------
    print(f"Escrito {OUT}")
    print(f"  reportes: {', '.join(p.name for p in sources)} (corte {CORTE})")
    print(f"  {len(rows)} filas inscripcion-asignatura, {len(ins_idx)} inscripciones"
          + (f" de {personas} personas ({len(ins_idx) - personas} cursan 2 carreras)" if personas else ""))
    print(f"  {len(carrera_keys)} carreras, {len(asignatura_keys)} asignaturas, {len(docente_keys)} docentes")
    print(f"  filas sin examen rendido (ex=0): {sin_examen} ({sin_examen / len(rows) * 100:.2f}%)")
    est_count = Counter(r[4] for r in rows)
    for i, lab in enumerate(ESTADO_LABELS):
        print(f"    {lab}: {est_count[i]} ({est_count[i] / len(rows) * 100:.2f}%)")
    mat_count = Counter(r[8] for r in rows)
    for i, lab in enumerate(MATRICULA_LABELS):
        print(f"    {lab}: {mat_count[i]} ({mat_count[i] / len(rows) * 100:.2f}%)")


if __name__ == "__main__":
    main()
