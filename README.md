# Dashboard Académico — Monitoreo Exámenes de Nivelación

Dashboard interactivo de resultados del Curso de Nivelación (1S2026), con vista general y vista
por carrera, 100% cross-filtrado (clic en cualquier gráfico filtra todo el dashboard). Construido
en HTML/CSS/JS vanilla, sin librerías ni build step, con la paleta institucional UNEMI.

## Ver el dashboard

https://evelyngarcia02.github.io/nivelacion/

## Qué muestra

**Vista General** (institucional, arranca sin ningún filtro):
- KPIs: estudiantes inscritos (con los que no tuvieron ninguna rendición como dato secundario), % que rindió examen,
  aprobados completamente, matrículas, % rindió / aprobado / reprobado, estudiantes "a un paso de
  aprobar" (nota entre 60 y 69), total de carreras.
- Resultado por Carrera y Resultado por Asignatura: mapas de calor (% Rindió / % Aprobado / %
  Reprobado) en una sola escala de color, ordenados por % de reprobación. Al pasar el cursor sobre
  el nombre de una carrera se ve su modalidad; sobre una celda, cuántos estudiantes fueron
  evaluados. Clic filtra todo el dashboard.
- ¿Con cuántos puntos de test llegaron al examen final?: mapa de calor que cruza cuántos de los 40
  puntos posibles en los 4 test (previos al examen) acumuló cada estudiante-curso, contra el
  resultado final.
- Brecha para aprobar: entre los reprobados, a cuántos puntos de los 70 necesarios se quedaron.

**Por Carrera**: buscador con menú desplegable de las 38 carreras (ordenadas por % de
reprobación). Al elegir una: KPIs de esa carrera, mapa de calor de asignaturas, tabla de detalle
por combinación asignatura + docente, y distribución de la nota final.

**Cross-filtering**: cualquier fila u celda clicable actúa como filtro global (carrera,
asignatura, docente, estado). Los filtros activos aparecen como chips debajo de las
pestañas y se quitan individualmente o todos a la vez.

## Fuente de datos

Los datos vienen del **SGA** (Sistema de Gestión Académica), no de Moodle. Moodle guarda la nota
tal como quedó en el examen, pero a algunos estudiantes se les ayudó después a subir la nota para
que aprueben; esa corrección solo queda reflejada en el SGA. Por eso el SGA es la fuente de verdad
del dashboard.

## Metodología de los cálculos

- `% Rindió Examen` = estudiantes-curso con estado `Aprobado` o `Reprobado` / total de
  estudiantes-curso (el resto quedó en curso, sin rendir el examen final).
- `% Aprobado` / `% Reprobado` = sobre estudiantes-curso que rindieron (no sobre el total).
- Identidad de estudiante: se usa `id_estudiante` (no la cédula) para agrupar filas de un mismo
  estudiante; ver el docstring de `scripts/build_data.py` para el detalle.
- Los nombres de carrera y asignatura de origen traían tildes inconsistentes/perdidas; se
  normalizan y corrigen con la ortografía oficial del informe (`CARRERA_FIX` / `ASIGNATURA_FIX`
  en `scripts/build_data.py`).

