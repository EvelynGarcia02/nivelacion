# Dashboard Académico — Monitoreo Exámenes de Nivelación

Dashboard interactivo de resultados del Curso de Nivelación (2S2026), con vista general y vista
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
asignatura, docente, estado, horario). Los filtros activos aparecen como chips debajo de las
pestañas y se quitan individualmente o todos a la vez.

## Metodología de los cálculos

Verificada contra el Informe Técnico ITI-DIPA-NVERAV-2026-004 hasta reproducir sus cifras exactas
(13.266 inscritos, 11.299 rindieron, 39.184 matrículas-curso, 84,80% rindió, 59,67% / 40,33%
aprobado/reprobado, 1.967 sin ninguna rendición):

- `% Rindió Examen` = estudiantes-curso con `numero_intento > 0` / total de estudiantes-curso.
- `% Aprobado` / `% Reprobado` = sobre estudiantes-curso que rindieron (no sobre el total).
- Las filas del CSV con cédula vacía se agrupan como **un único** estudiante compartido (no se
  ignoran ni se cuentan como estudiantes distintos) — así es como lo calcula el dashboard
  institucional de origen; ver el docstring de `scripts/build_data.py` para el detalle.
- Los nombres de carrera y asignatura del CSV traían tildes inconsistentes/perdidas; se
  normalizan y corrigen con la ortografía oficial del informe (`CARRERA_FIX` / `ASIGNATURA_FIX`
  en `scripts/build_data.py`).

