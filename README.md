# Dashboard Académico — Monitoreo Exámenes de Nivelación

Dashboard interactivo de resultados del Curso de Nivelación (2S2026), con vista general y vista
por carrera, 100% cross-filtrado (clic en cualquier gráfico filtra todo el dashboard). Construido
en HTML/CSS/JS vanilla, sin librerías ni build step, con la paleta institucional UNEMI.

## Ver el dashboard

Abrí `index.html` con doble clic en el explorador de archivos. No necesita servidor ni
instalación: los datos ya vienen embebidos en `js/data.js`, así que funciona directo desde el
disco o publicado como sitio estático (GitHub Pages, etc.).

## Qué muestra

**Vista General** (institucional, arranca sin ningún filtro):
- KPIs: estudiantes inscritos (con la deserción total como dato secundario), % que rindió examen,
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

## Estructura del repositorio

```
index.html          punto de entrada
css/styles.css       estilos (paleta UNEMI, KPIs, mapas de calor, etc.)
js/app.js            toda la lógica del dashboard (filtros, agregación, render)
js/data.js           dataset agregado y anonimizado (sin nombres ni cédulas), generado
assets/logo_unemi.png logo institucional
scripts/build_data.py script que genera js/data.js a partir del CSV fuente
data/                 NO está en este repo (ver abajo)
```

`data/` (el CSV fuente, el informe PDF y las capturas) se mantiene **fuera del repositorio**
(`.gitignore`) porque son insumos internos de trabajo, no porque el dashboard los necesite para
funcionar: `js/data.js` ya trae los datos agregados y anonimizados que el sitio usa.

## Actualizar los datos (nuevo período, correcciones, etc.)

1. Colocá `curso_nivelacion_<periodo>.csv` en una carpeta local `data/` (mismo formato de
   columnas; esa carpeta no se sube al repo).
2. Instalá dependencias una vez: `pip install pandas`
3. Ajustá el nombre del archivo en `scripts/build_data.py` (constante `CSV`) si cambia, y corré:
   `python scripts/build_data.py` → regenera `js/data.js`. Recargá `index.html` para ver los
   cambios. El script imprime un resumen (filas, estudiantes, carreras/asignaturas/docentes) para
   verificar rápido que la carga fue consistente.
4. Commiteá y subí el `js/data.js` actualizado (ese sí va al repo).

Si aparecen carreras o asignaturas nuevas que el script no reconoce en `CARRERA_FIX` /
`ASIGNATURA_FIX`, se muestran igual (con mejor esfuerzo de capitalización), solo que sin la
corrección ortográfica manual — se puede agregar la entrada correspondiente en esas listas.
