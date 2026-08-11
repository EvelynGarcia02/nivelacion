# Dashboard Académico — Monitoreo Exámenes de Nivelación

Dashboard interactivo de resultados del Curso de Nivelación (1S2026), con vista general y vista
por carrera, 100% cross-filtrado (clic en cualquier gráfico filtra todo el dashboard). Construido
en HTML/CSS/JS vanilla, sin librerías ni build step, con la paleta institucional UNEMI.

## Ver el dashboard

https://evelyngarcia02.github.io/nivelacion/

## Qué muestra

**Vista General** (institucional, arranca sin ningún filtro):
- KPIs: total de inscritos, los tres estados del SGA (% Aprobado / % Reprobado / % En curso, que
  suman 100%) y total de matrículas. Debajo, a nivel de inscripción: cuántos aprobaron todas sus
  asignaturas, a cuántos les quedó una sola, cuántos no se presentaron a ningún examen, cuántas
  matrículas son repetición y el total de carreras.
- Calificaciones sin cerrar: qué carrera, asignatura y docente siguen con matrículas "En curso",
  o sea sin notas cerradas en el SGA. La tarjeta no aparece si no hay ninguna.
- Resultado por Carrera y Resultado por Asignatura: mapas de calor (% Aprobado / % Reprobado / %
  En curso sobre el total) en una sola escala de color, ordenados por % de reprobación. Al pasar el
  cursor sobre el nombre de una carrera se ve su modalidad. Clic filtra todo el dashboard.
- Resultado por número de matrícula: si el estudiante cursa esa asignatura por primera, segunda o
  tercera vez.
- ¿Con cuántos puntos de test llegaron al examen final?: mapa de calor que cruza cuántos de los 40
  puntos posibles en los 4 test (previos al examen) acumuló cada estudiante-curso, contra el
  resultado final.
- Brecha para aprobar: entre quienes se presentaron y reprobaron, a cuántos puntos de los 70
  necesarios se quedaron.

**Por Carrera**: buscador con menú desplegable de las 38 carreras (ordenadas por % de
reprobación). Al elegir una: KPIs de esa carrera —incluido el **% que rindió el examen**, que no
está en la vista general—, mapa de calor de asignaturas, tabla de detalle por combinación
asignatura + docente, y distribución de la nota final.

**Cross-filtering**: cualquier fila u celda clicable actúa como filtro global (carrera,
asignatura, docente, estado, número de matrícula). Los filtros activos aparecen como chips debajo
de las pestañas y se quitan individualmente o todos a la vez.

## Fuente de datos

Los datos vienen del **SGA** (Sistema de Gestión Académica), no de Moodle. Moodle guarda la nota
tal como quedó en el examen, pero a algunos estudiantes se les ayudó después a subir la nota para
que aprueben; esa corrección solo queda reflejada en el SGA. Por eso el SGA es la fuente de verdad
del dashboard.

`js/data.js` se genera con `python scripts/build_data.py`, que lee los reportes del SGA que estén
en `data/curso_niv_1S2026_sga*.csv` (o `.xlsx`) — salida de la query `est_cal_sga_niv_grado.sql`.
Hoy es `curso_niv_1S2026_sga_ins.csv`: **las 38 carreras, actas ya cerradas** (corte del
11/08/2026) y a nivel de inscripción.

El script acepta varios archivos a la vez (sirve un export partido por grupos de carreras) y sobre
cada uno hace dos controles que avisa por consola: ignora los que no traigan las columnas
necesarias — entre ellas `inscripcion_id`, así un export viejo olvidado en `data/` no duplica
filas — y nombra las carreras del informe que no aparezcan en ningún reporte, para que un export
parcial no achique el dashboard en silencio.

## Metodología de los cálculos

- **Los estados son los del SGA tal cual** (`Aprobado` / `Reprobado` / `En curso`) y los
  porcentajes son **sobre el total**, así que suman 100%: 58,03% / 41,90% / 0,07% en el corte del
  11/08/2026. Al que no se presentó al examen el SGA lo reprueba, y el dashboard respeta ese
  criterio en vez de contarlo aparte.
- **`En curso`** con el periodo ya cerrado no significa que al estudiante le falte rendir, sino que
  **el docente no cerró las calificaciones** de esa materia. Por eso se muestra como estado propio
  y tiene su tarjeta con nombre y apellido, en vez de fundirlo con reprobado.
- **`% Rindió el examen`** (solo en la vista Por Carrera) = matrículas con `ex > 0` / total.
  Presentarse o no al examen no es un estado, es un dato aparte: se verificó contra el corte del
  30/07 que las 32.926 filas calificadas tienen `ex > 0` y las 5.731 `EN CURSO` tienen todas
  `ex = 0`, y que entre las filas con `ex = 0` la nota final máxima es 40, o sea solo puntos de
  test. Ese mismo criterio deja fuera a los ausentes de la brecha para aprobar, del histograma de
  notas y del cruce de puntos de test, para no mezclarlos con quienes rindieron y no alcanzaron.
- Identidad de estudiante: se agrupa por **`inscripcion_id`** (la matrícula de una persona en una
  carrera), no por persona ni por cédula. Una misma persona puede estar inscrita en dos carreras a
  la vez y cursar la misma asignatura en ambas: son 12 personas sobre 13.136 inscripciones, y
  agruparlas por persona las fusionaba, subcontaba estudiantes y podía arruinar "aprobados
  completamente" (aprobar todo en una carrera y no en la otra). Cada inscripción pertenece a una
  sola carrera, así que es la unidad correcta para todo lo que el dashboard llama "estudiante".
- Los nombres de carrera y asignatura de origen traían tildes inconsistentes/perdidas; se
  normalizan y corrigen con la ortografía oficial del informe (`CARRERA_FIX` / `ASIGNATURA_FIX`
  en `scripts/build_data.py`).

