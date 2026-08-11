/* Requiere que js/data.js se cargue antes y defina la constante global DATA.
   Fila de DATA.rows: [inscripcionIdx, carreraIdx, asignaturaIdx, docenteIdx, estadoIdx, notaFinal, testProm, examenFinal]
   estadoIdx: 0 Aprobado, 1 Reprobado, 2 No realizó examen

   R.SID identifica a la INSCRIPCION (persona + carrera), no a la persona: hay
   estudiantes inscritos en dos carreras a la vez, y cada carrera es una cuenta
   aparte. Ver el docstring de scripts/build_data.py. */

const R = {SID:0, CARRERA:1, ASIG:2, DOC:3, ESTADO:4, NOTA:5, TESTPROM:6, EXAMEN:7};
const EST = {APROBADO:0, REPROBADO:1, NORINDIO:2};

/* ---------- helpers genericos ---------- */
function el(tag, attrs, children){
  const e = document.createElement(tag);
  if(attrs) for(const k in attrs){
    if(k==='class') e.className = attrs[k];
    else if(k==='style') e.style.cssText = attrs[k];
    else if(k.startsWith('on')) e.addEventListener(k.slice(2), attrs[k]);
    else e.setAttribute(k, attrs[k]);
  }
  if(children!=null) (Array.isArray(children)?children:[children]).forEach(c=>{
    if(c==null) return;
    e.appendChild(typeof c==='string' || typeof c==='number' ? document.createTextNode(c) : c);
  });
  return e;
}
const ICON_PATHS = {
  clipboard:'<path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="m9 14 2 2 4-4"/>',
  trending:'<path d="M3 17l6-6 4 4 8-8"/><path d="M17 7h4v4"/>',
  award:'<circle cx="12" cy="8" r="6"/><path d="M8.5 13.5 7 22l5-3 5 3-1.5-8.5"/>',
  users:'<path d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  bars:'<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
  layers:'<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
  scale:'<line x1="7" y1="20" x2="7" y2="10"/><line x1="17" y1="20" x2="17" y2="4"/><line x1="2" y1="20" x2="22" y2="20"/>',
  alert:'<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  check:'<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
  list:'<path d="m3 7 2 2 4-4"/><path d="M13 6h8"/><path d="m3 15 2 2 4-4"/><path d="M13 16h8"/>',
  clock:'<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  search:'<circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
  download:'<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
};
function icon(name){
  const wrap = document.createElement('div');
  wrap.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICON_PATHS[name]||''}</svg>`;
  return wrap.firstElementChild;
}
function iconBadge(name){
  const badge = el('div',{class:'icon-badge'});
  badge.appendChild(icon(name));
  return badge;
}
const tooltip = document.getElementById('tooltip');
function showTip(evt, text){
  tooltip.textContent = text;
  tooltip.style.display = 'block';
  const x = evt.clientX, y = evt.clientY;
  tooltip.style.left = Math.min(x+12, window.innerWidth-270)+'px';
  tooltip.style.top = (y+16)+'px';
}
function hideTip(){ tooltip.style.display='none'; }
function attachTip(elm, text){
  elm.addEventListener('mousemove', e=>showTip(e,text));
  elm.addEventListener('mouseleave', hideTip);
}
function fmt1(n){ if(n==null || isNaN(n)) return '—'; return (Math.round(n*10)/10).toString().replace(/\.0$/,''); }
function fmt2(n){ if(n==null || isNaN(n)) return '—'; return (Math.round(n*100)/100).toFixed(2); }
function fmtInt(n){ return n.toLocaleString('es-EC'); }

/* escala de riesgo: 0% (verde, aprobado) -> 50% (ambar) -> 100% (rojo, reprobado). Se usa
   en barras de ranking (hbar-fill) y en las pastillas de la tabla de docentes. */
function riskColor(pct){
  if(pct==null || isNaN(pct)) return 'var(--estado-norindio)';
  const p = Math.max(0, Math.min(100, pct));
  if(p<=50){
    const t = p/50*100;
    return `color-mix(in srgb, var(--estado-cerca) ${t}%, var(--estado-aprobado) ${100-t}%)`;
  }
  const t = (p-50)/50*100;
  return `color-mix(in srgb, var(--estado-reprobado) ${t}%, var(--estado-cerca) ${100-t}%)`;
}

/* escala monocromatica (un solo tono, mas intenso a mayor %) para TODAS las celdas de mapas
   de calor: nada de verde/ambar/rojo alli, solo intensidad de --series-1. */
function heatColor(pct){
  if(pct==null || isNaN(pct)) return 'var(--surface-1)';
  const p = Math.max(0, Math.min(100, pct));
  return `color-mix(in srgb, var(--series-1) ${p}%, var(--surface-1))`;
}

/* ---------- estado de filtros globales (cross-filter tipo PowerBI) ---------- */
const F = {carrera:null, asignatura:null, docente:null, estado:null};
function isPrinting(){ return document.body.classList.contains('printing-carrera'); }

function rowMatches(r, exclude){
  if(!exclude.has('carrera') && F.carrera!=null && r[R.CARRERA]!==F.carrera) return false;
  if(!exclude.has('asignatura') && F.asignatura!=null && r[R.ASIG]!==F.asignatura) return false;
  if(!exclude.has('docente') && F.docente!=null && r[R.DOC]!==F.docente) return false;
  if(!exclude.has('estado') && F.estado!=null && r[R.ESTADO]!==F.estado) return false;
  return true;
}
const NO_EXCLUDE = new Set();
function filteredRows(exclude){
  exclude = exclude || NO_EXCLUDE;
  return DATA.rows.filter(r=>rowMatches(r, exclude));
}
function toggleFilter(dim, value){
  F[dim] = (F[dim]===value) ? null : value;
  rerender();
}
function clearFilter(dim){ F[dim]=null; rerender(); }

/* ---------- agregacion ---------- */
function emptyAgg(){ return {total:0, aprobado:0, reprobado:0, norindio:0, notaSum:0, notaN:0, students:new Set()}; }
function addRow(agg, r){
  agg.total++;
  agg.students.add(r[R.SID]);
  if(r[R.ESTADO]===EST.APROBADO){ agg.aprobado++; agg.notaSum+=r[R.NOTA]; agg.notaN++; }
  else if(r[R.ESTADO]===EST.REPROBADO){ agg.reprobado++; agg.notaSum+=r[R.NOTA]; agg.notaN++; }
  else agg.norindio++;
}
function aggStats(agg){
  const rindio = agg.aprobado+agg.reprobado;
  return {
    total: agg.total, rindio, aprobado: agg.aprobado, reprobado: agg.reprobado, norindio: agg.norindio,
    nStudents: agg.students.size,
    pctRindio: agg.total? rindio/agg.total*100 : null,
    pctAprobado: rindio? agg.aprobado/rindio*100 : null,
    pctReprobado: rindio? agg.reprobado/rindio*100 : null,
    pctNorindio: agg.total? agg.norindio/agg.total*100 : null,
    notaProm: agg.notaN? agg.notaSum/agg.notaN : null,
  };
}
function groupBy(rows, keyFn){
  const m = new Map();
  rows.forEach(r=>{
    const k = keyFn(r);
    if(k==null) return;
    if(!m.has(k)) m.set(k, emptyAgg());
    addRow(m.get(k), r);
  });
  return m;
}
function computeKpis(rows){
  const agg = emptyAgg();
  rows.forEach(r=>addRow(agg,r));
  const stats = aggStats(agg);
  const sm = new Map();
  rows.forEach(r=>{
    const sid=r[R.SID], e=r[R.ESTADO];
    if(!sm.has(sid)) sm.set(sid, {rindio:false, allAp:true});
    const s = sm.get(sid);
    if(e===EST.APROBADO || e===EST.REPROBADO) s.rindio = true;
    if(e!==EST.APROBADO) s.allAp = false;
  });
  let totalEst = sm.size, rindioEst = 0, totalAp = 0;
  sm.forEach(s=>{ if(s.rindio) rindioEst++; if(s.allAp) totalAp++; });
  const cercaAprobar = rows.filter(r=>(r[R.ESTADO]===EST.APROBADO||r[R.ESTADO]===EST.REPROBADO) && r[R.NOTA]>=60 && r[R.NOTA]<70).length;
  const evaluados = agg.aprobado+agg.reprobado;
  return {
    stats, totalEst, rindioEst, totalAp, sinRendicion: totalEst-rindioEst, cercaAprobar, evaluados,
    nCarreras: new Set(rows.map(r=>r[R.CARRERA])).size,
    nAsignaturas: new Set(rows.map(r=>r[R.ASIG])).size,
    nDocentes: new Set(rows.map(r=>r[R.DOC])).size,
  };
}

/* ---------- KPI row builder ---------- */
function kpiRow(items){
  const row = el('div',{class:'kpi-row'});
  items.forEach(it=>{
    const top = el('div',{class:'kpi-top'});
    if(it.icon) top.appendChild(iconBadge(it.icon));
    top.appendChild(el('div',{class:'label'}, it.label));
    const box = el('div',{class:'kpi'+(it.accent?' accent':'')},[top, el('div',{class:'value'}, it.value)]);
    if(it.delta!=null) box.appendChild(el('div',{class:'delta '+(it.deltaGood?'good':'bad')}, it.delta));
    if(it.sub) box.appendChild(el('div',{class:'sub'}, it.sub));
    row.appendChild(box);
  });
  return row;
}

/* ---------- filtro: barra de chips activos (compartida por ambas vistas) ---------- */
const filterBarEl = document.getElementById('filterBar');
const FILTER_LABELS = {
  carrera: v=>'Carrera: '+DATA.dict.carrera[v],
  asignatura: v=>'Asignatura: '+DATA.dict.asignatura[v],
  docente: v=>'Docente: '+DATA.dict.docente[v],
  estado: v=>'Estado: '+DATA.dict.estado[v],
};
function renderFilterBar(){
  filterBarEl.innerHTML = '';
  const dims = Object.keys(F).filter(k=>F[k]!=null);
  if(!dims.length) return;
  dims.forEach(dim=>{
    filterBarEl.appendChild(el('button',{class:'filter-chip', onclick:()=>clearFilter(dim)},
      [FILTER_LABELS[dim](F[dim]), el('span',{class:'x'},'✕')]));
  });
  if(dims.length>1){
    filterBarEl.appendChild(el('button',{class:'filter-chip clear-all', onclick:()=>{Object.keys(F).forEach(k=>F[k]=null); rerender();}}, 'Limpiar todos los filtros'));
  }
}

/* ---------- mapa de calor: % Rindió / % Aprobado / % Reprobado por carrera o asignatura ---------- */
function heatmap3Card(opts){
  // opts: {title, caption, iconName, rows, dim ('carrera'|'asignatura'), labelFn}
  const card = el('div',{class:'card'});
  card.appendChild(el('h2',null,[iconBadge(opts.iconName), opts.title]));
  if(opts.caption) card.appendChild(el('p',{class:'caption'},opts.caption));
  const dimField = opts.dim==='carrera'? R.CARRERA : R.ASIG;
  const grouped = groupBy(opts.rows, r=>r[dimField]);
  let list = [...grouped.entries()].map(([idx,agg])=>({idx, ...aggStats(agg)}));
  list.sort((a,b)=>(b.pctReprobado??-1)-(a.pctReprobado??-1));
  if(isPrinting() && F[opts.dim]!=null){
    list = list.filter(x=>x.idx===F[opts.dim]);
  }
  if(!list.length){ card.appendChild(el('div',{class:'empty-note'},'Sin datos para este filtro.')); return card; }
  const activeVal = F[opts.dim];
  function cell(x, pct, num, den, detailLabel){
    const color = heatColor(pct);
    const textColor = pct!=null && pct>=50 ? '#fff' : 'var(--text-primary)';
    const td = el('td',{class:'heat-cell', style:`background:${color};color:${textColor}`}, pct!=null?fmt2(pct)+'%':'—');
    attachTip(td, opts.labelFn(x.idx)+' — '+(pct!=null?fmt2(pct)+'% ':'')+detailLabel+' ('+fmtInt(num)+' de '+fmtInt(den)+')');
    return td;
  }
  const tableWrap = el('div',{class:'table-scroll'});
  const table = el('table',{class:'datatable heatmap'});
  table.appendChild(el('tr',null,[el('th',null,opts.dim==='carrera'?'Carrera':'Asignatura'), el('th',null,'% Rindió'), el('th',null,'% Aprobado'), el('th',null,'% Reprobado')]));
  list.forEach(x=>{
    const isSel = activeVal===x.idx;
    const tr = el('tr',{class:'clickable'+(isSel?' selected':''), onclick:()=>toggleFilter(opts.dim, x.idx)});
    const labelTd = el('td',null, opts.labelFn(x.idx));
    if(opts.extraInfoFn) attachTip(labelTd, opts.labelFn(x.idx)+' — '+opts.extraInfoFn(x.idx));
    tr.appendChild(labelTd);
    tr.appendChild(cell(x, x.pctRindio, x.rindio, x.total, 'rindieron'));
    tr.appendChild(cell(x, x.pctAprobado, x.aprobado, x.rindio, 'aprobaron'));
    tr.appendChild(cell(x, x.pctReprobado, x.reprobado, x.rindio, 'reprobaron'));
    table.appendChild(tr);
  });
  tableWrap.appendChild(table);
  card.appendChild(tableWrap);
  return card;
}

/* ---------- histograma nota final ---------- */
function notaHistCard(rows){
  const card = el('div',{class:'card'});
  card.appendChild(el('h2',null,[iconBadge('bars'),'Distribución de la nota final']));
  card.appendChild(el('p',{class:'caption'},'Solo estudiantes-curso que rindieron el examen final. Nota mínima de aprobación: 70/100 (Art. 59, Reglamento de Admisión y Nivelación). La franja 60–69 es la zona de "casi aprobados".'));
  const scored = rows.filter(r=>r[R.ESTADO]===EST.APROBADO || r[R.ESTADO]===EST.REPROBADO);
  const labels = ['0-9','10-19','20-29','30-39','40-49','50-59','60-69','70-79','80-89','90-99','100+'];
  const counts = new Array(11).fill(0);
  scored.forEach(r=>{ let bi = Math.floor(r[R.NOTA]/10); if(bi<0) bi=0; if(bi>10) bi=10; counts[bi]++; });
  const max = Math.max(1, ...counts);
  const wrap = el('div',{class:'gbar-wrap'});
  labels.forEach((lab,i)=>{
    const cat = el('div',{class:'gbar-cat'});
    const bars = el('div',{class:'gbar-bars'});
    const h = counts[i]/max*100;
    const color = i===6 ? 'var(--estado-cerca)' : (i<7 ? 'var(--estado-reprobado)' : 'var(--estado-aprobado)');
    const col = el('div',{class:'gbar-col wide', style:`height:${h}%;background:${color}`});
    col.appendChild(el('div',{class:'val'}, fmtInt(counts[i])));
    attachTip(col, labels[i]+' puntos: '+fmtInt(counts[i])+' estudiantes-curso');
    bars.appendChild(col);
    cat.appendChild(bars);
    wrap.appendChild(cat);
  });
  card.appendChild(wrap);
  const axis = el('div',{class:'gbar-axis'});
  labels.forEach(l=>axis.appendChild(el('span',null,l)));
  card.appendChild(axis);
  const cerca = counts[6];
  card.appendChild(el('div',{class:'callout warn', style:'margin-top:14px;'},[
    el('div',{class:'big'}, fmtInt(cerca)+' estudiantes-curso "a un paso de aprobar" (60–69 pts)'),
    el('div',{class:'txt'},'Con una intervención dirigida (refuerzo puntual, recuperación de participación) este grupo es el de mayor probabilidad de conversión a aprobado.'),
  ]));
  return card;
}

/* ---------- con cuantos puntos de test llegaron al examen ---------- */
function testParticipacionCard(rows){
  const card = el('div',{class:'card'});
  card.appendChild(el('h2',null,[iconBadge('grid'),'¿Con cuántos puntos de test llegaron al examen final?']));
  card.appendChild(el('p',{class:'caption'},'Los 4 test de cada asignatura suman hasta 40 puntos en total (10 c/u) y se rinden ANTES del examen final. Cada fila agrupa a los estudiantes-curso según cuántos de esos 40 puntos acumularon; cada celda es el % de ese grupo que terminó en ese resultado (pasá el cursor para ver el total).'));
  const testTotal = r=>r[R.TESTPROM]*4; // suma aproximada de test1..test4 (0-40); testProm ya es su promedio 0-10
  const rowDefs = [
    {label:'0 puntos — no hizo ningún test', test:r=>testTotal(r)<=0},
    {label:'1 a 9 puntos', test:r=>testTotal(r)>0 && testTotal(r)<10},
    {label:'10 a 19 puntos', test:r=>testTotal(r)>=10 && testTotal(r)<20},
    {label:'20 a 29 puntos', test:r=>testTotal(r)>=20 && testTotal(r)<30},
    {label:'30 a 40 puntos', test:r=>testTotal(r)>=30},
  ];
  const colDefs = [
    {label:'% Aprobó', estVal:EST.APROBADO},
    {label:'% Reprobó', estVal:EST.REPROBADO},
    {label:'% No rindió examen', estVal:EST.NORINDIO},
  ];
  if(!rows.length){ card.appendChild(el('div',{class:'empty-note'},'Sin datos para este filtro.')); return card; }
  const table = el('table',{class:'datatable heatmap'});
  table.appendChild(el('tr',null,[el('th',null,''), ...colDefs.map(c=>el('th',null,c.label))]));
  rowDefs.forEach(rd=>{
    const rowRows = rows.filter(rd.test);
    const rowTotal = rowRows.length;
    const tr = el('tr',null,[el('td',null,[el('b',null,rd.label), el('div',{class:'heat-comp-n'}, fmtInt(rowTotal)+' estudiantes-curso')])]);
    colDefs.forEach(cd=>{
      const n = rowRows.filter(r=>r[R.ESTADO]===cd.estVal).length;
      const pct = rowTotal? n/rowTotal*100 : null;
      const bg = heatColor(pct);
      const textColor = pct!=null && pct>=50 ? '#fff' : 'var(--text-primary)';
      const td = el('td',{class:'heat-cell', style:`background:${bg};color:${textColor}`}, pct!=null?fmt2(pct)+'%':'—');
      attachTip(td, rd.label+' — '+cd.label+': '+fmtInt(n)+' de '+fmtInt(rowTotal)+(pct!=null?' ('+fmt2(pct)+'%)':''));
      tr.appendChild(td);
    });
    table.appendChild(tr);
  });
  card.appendChild(table);
  const bajos = rows.filter(r=>testTotal(r)>0 && testTotal(r)<10 && (r[R.ESTADO]===EST.APROBADO||r[R.ESTADO]===EST.REPROBADO));
  const bajosAprobaron = bajos.filter(r=>r[R.ESTADO]===EST.APROBADO);
  const altos = rows.filter(r=>testTotal(r)>=30 && (r[R.ESTADO]===EST.APROBADO||r[R.ESTADO]===EST.REPROBADO));
  const altosAprobaron = altos.filter(r=>r[R.ESTADO]===EST.APROBADO);
  if(bajos.length && altos.length){
    card.appendChild(el('p',{class:'caption', style:'margin-top:12px;'},
      'Dato puntual: entre quienes acumularon de 1 a 9 puntos en los test y rindieron el examen, '+fmt2(bajosAprobaron.length/bajos.length*100)+'% aprobó la asignatura; entre quienes acumularon 30 a 40 puntos, '+fmt2(altosAprobaron.length/altos.length*100)+'% aprobó.'
    ));
  }
  return card;
}

/* ---------- brecha para aprobar: a cuantos puntos de 70 se quedaron los reprobados ---------- */
function brechaAprobarCard(rows){
  const card = el('div',{class:'card'});
  card.appendChild(el('h2',null,[iconBadge('scale'),'Brecha para aprobar']));
  card.appendChild(el('p',{class:'caption'},'Entre los estudiantes-curso que reprobaron el examen final, a cuántos puntos de los 70 necesarios (Art. 59, Reglamento de Admisión y Nivelación) se quedaron.'));
  const reprobados = rows.filter(r=>r[R.ESTADO]===EST.REPROBADO);
  if(!reprobados.length){ card.appendChild(el('div',{class:'empty-note'},'Sin reprobados para este filtro.')); return card; }
  const buckets = [
    {label:'Menos de 5 puntos', axis:'< 5', test:g=>g<5, color:'var(--estado-cerca)'},
    {label:'Entre 5 y 10 puntos', axis:'5-10', test:g=>g>=5&&g<10, color:'var(--estado-cerca)'},
    {label:'Entre 10 y 15 puntos', axis:'10-15', test:g=>g>=10&&g<15, color:'var(--estado-reprobado)'},
    {label:'Entre 15 y 20 puntos', axis:'15-20', test:g=>g>=15&&g<20, color:'var(--estado-reprobado)'},
    {label:'20 puntos o más', axis:'20+', test:g=>g>=20, color:'var(--estado-reprobado)'},
  ];
  const counts = new Array(buckets.length).fill(0);
  reprobados.forEach(r=>{
    const gap = 70 - r[R.NOTA];
    const bi = buckets.findIndex(b=>b.test(gap));
    if(bi>=0) counts[bi]++;
  });
  const max = Math.max(1, ...counts);
  const wrap = el('div',{class:'gbar-wrap'});
  buckets.forEach((b,i)=>{
    const cat = el('div',{class:'gbar-cat'});
    const bars = el('div',{class:'gbar-bars'});
    const h = counts[i]/max*100;
    const col = el('div',{class:'gbar-col wide', style:`height:${h}%;background:${b.color}`});
    col.appendChild(el('div',{class:'val'}, fmtInt(counts[i])));
    attachTip(col, b.label+': '+fmtInt(counts[i])+' estudiantes-curso ('+fmt2(counts[i]/reprobados.length*100)+'% de los reprobados)');
    bars.appendChild(col);
    cat.appendChild(bars);
    wrap.appendChild(cat);
  });
  card.appendChild(wrap);
  const axis = el('div',{class:'gbar-axis'});
  buckets.forEach(b=>axis.appendChild(el('span',null,b.axis)));
  card.appendChild(axis);
  const cerca = counts[0]+counts[1];
  card.appendChild(el('div',{class:'callout warn', style:'margin-top:14px;'},[
    el('div',{class:'big'}, fmtInt(cerca)+' estudiantes-curso reprobaron por menos de 10 puntos'),
    el('div',{class:'txt'},'Sobre un total de '+fmtInt(reprobados.length)+' reprobados en el filtro actual.'),
  ]));
  return card;
}

/* ================= VISTA GENERAL ================= */
const gView = document.getElementById('view-global');

function renderGlobal(){
  gView.innerHTML = '';
  gView.appendChild(el('div',{class:'print-section-banner'},'1. Vista General'));
  const rows = filteredRows();
  const k = computeKpis(rows);

  gView.appendChild(kpiRow([
    {label:'Total de estudiantes inscritos', icon:'users', value: fmtInt(k.totalEst), sub: k.totalEst? fmtInt(k.sinRendicion)+' sin ninguna rendición ('+fmt2(k.sinRendicion/k.totalEst*100)+'%)':'', accent:true},
    {label:'% que rindió examen (al menos 1 curso)', icon:'check', value: k.totalEst? fmt2(k.rindioEst/k.totalEst*100)+'%':'—', sub: fmtInt(k.rindioEst)+' de '+fmtInt(k.totalEst)+' estudiantes'},
    {label:'Aprobados completamente (todas sus materias)', icon:'award', value: fmtInt(k.totalAp)},
    {label:'Total de matrículas (estudiante-curso)', icon:'clipboard', value: fmtInt(k.stats.total)},
    {label:'% Rindió examen (estudiante-curso)', icon:'check', value: k.stats.pctRindio!=null?fmt2(k.stats.pctRindio)+'%':'—', sub: fmtInt(k.stats.rindio)+' de '+fmtInt(k.stats.total)},
  ]));
  gView.appendChild(kpiRow([
    {label:'% Aprobado (sobre quienes rindieron)', icon:'award', value: k.stats.pctAprobado!=null?fmt2(k.stats.pctAprobado)+'%':'—'},
    {label:'% Reprobado (sobre quienes rindieron)', icon:'alert', value: k.stats.pctReprobado!=null?fmt2(k.stats.pctReprobado)+'%':'—'},
    {label:'Estudiantes "a un paso de aprobar"', icon:'scale', value: fmtInt(k.cercaAprobar), sub:'nota final entre 60 y 69.9'},
    {label:'Carreras', icon:'grid', value: k.nCarreras},
  ]));

  const rankGrid = el('div',{class:'grid-2'});
  rankGrid.appendChild(heatmap3Card({
    title:'Resultado por Carrera', iconName:'grid', dim:'carrera', labelFn:i=>DATA.dict.carrera[i],
    caption:'Ordenado por % de reprobación. Pasá el cursor sobre el nombre de la carrera para ver su modalidad, y sobre una celda para ver cuántos estudiantes fueron evaluados. Clic para filtrar todo el dashboard.',
    rows: filteredRows(new Set(['carrera'])),
    extraInfoFn: i=>DATA.dict.carreraModalidad[i],
  }));
  rankGrid.appendChild(heatmap3Card({
    title:'Resultado por Asignatura', iconName:'grid', dim:'asignatura', labelFn:i=>DATA.dict.asignatura[i],
    caption:'Ordenado por % de reprobación. Pasá el cursor sobre una celda para ver cuántos estudiantes fueron evaluados. Clic para filtrar todo el dashboard.',
    rows: filteredRows(new Set(['asignatura'])),
  }));
  gView.appendChild(rankGrid);

  const bottomGrid = el('div',{class:'grid-2'});
  bottomGrid.appendChild(testParticipacionCard(rows));
  bottomGrid.appendChild(brechaAprobarCard(rows));
  gView.appendChild(bottomGrid);
}

/* ================= POR CARRERA ================= */
const cView = document.getElementById('view-carrera');
const comboWrap = el('div',{class:'combo-wrap'});
const selSearch = el('input',{class:'sel-search', placeholder:'Buscar carrera...', autocomplete:'off'});
const dropdownMenu = el('div',{class:'dropdown-menu'});
comboWrap.appendChild(selSearch);
comboWrap.appendChild(dropdownMenu);
const pdfBtn = el('button',{class:'pdf-btn', type:'button', onclick:()=>downloadCarreraPDF()},[icon('download'), 'Descargar reporte PDF']);
const carreraToolbar = el('div',{class:'carrera-toolbar'});
carreraToolbar.appendChild(comboWrap);
carreraToolbar.appendChild(pdfBtn);
const carreraBody = el('div',null,null);
cView.appendChild(carreraToolbar);
cView.appendChild(carreraBody);

/* ---------- reporte PDF (impresion): incluye Vista General (siempre) + Detalle por Carrera (si hay una seleccionada) ---------- */
const printHeader = el('div',{class:'print-header'});
const wrapEl = document.querySelector('.wrap');
wrapEl.insertBefore(printHeader, wrapEl.firstChild);

let printOriginalTitle = document.title;
function downloadCarreraPDF(){
  const cIdx = F.carrera;
  printHeader.innerHTML = '';
  printHeader.appendChild(el('div',{class:'ph-top'},[
    el('img',{class:'ph-logo', src:'assets/logo_unemi.png', alt:'UNEMI'}),
    el('div',{class:'ph-titles'},[
      el('h1',null,'Reporte Académico'),
      el('div',{class:'sub'}, cIdx!=null
        ? 'Vista General y Detalle por Carrera: '+DATA.dict.carrera[cIdx]+' ('+DATA.dict.carreraModalidad[cIdx]+')'
        : 'Vista General'),
    ]),
  ]));
  cView.classList.toggle('print-hide-section', cIdx==null);
  printOriginalTitle = document.title;
  document.title = ' ';
  document.body.classList.add('printing-carrera');
  rerender();
  window.print();
}
window.addEventListener('afterprint', ()=>{
  document.body.classList.remove('printing-carrera');
  cView.classList.remove('print-hide-section');
  document.title = printOriginalTitle;
  rerender();
});

const CARRERA_STATS_ALL = (()=>{
  const grouped = groupBy(DATA.rows, r=>r[R.CARRERA]);
  const arr = new Array(DATA.dict.carrera.length).fill(null);
  grouped.forEach((agg,idx)=>{ arr[idx] = aggStats(agg); });
  return arr;
})();
const CARRERA_ORDER = [...DATA.dict.carrera.keys()].sort((a,b)=>{
  const pa = CARRERA_STATS_ALL[a] ? (CARRERA_STATS_ALL[a].pctReprobado??-1) : -1;
  const pb = CARRERA_STATS_ALL[b] ? (CARRERA_STATS_ALL[b].pctReprobado??-1) : -1;
  return pb-pa;
});

function selectCarrera(idx){
  F.carrera = idx;
  selSearch.value = '';
  closeDropdown();
  rerender();
}
function openDropdown(){ dropdownMenu.classList.add('open'); buildDropdown(); }
function closeDropdown(){ dropdownMenu.classList.remove('open'); }
function buildDropdown(){
  dropdownMenu.innerHTML = '';
  const q = selSearch.value.trim().toLowerCase();
  const scopeRows = filteredRows(new Set(['carrera']));
  const grouped = groupBy(scopeRows, r=>r[R.CARRERA]);
  let any = false;
  CARRERA_ORDER.forEach(idx=>{
    const label = DATA.dict.carrera[idx];
    if(q && !label.toLowerCase().includes(q)) return;
    any = true;
    const s = aggStats(grouped.get(idx) || emptyAgg());
    const item = el('div',{class:'dropdown-item'+(F.carrera===idx?' active':''), onclick:()=>selectCarrera(idx)},[
      el('span',{class:'dd-dot', style:`background:${riskColor(s.pctReprobado)}`}),
      el('span',{class:'dd-label'}, label),
      el('span',{class:'dd-sub'}, fmtInt(s.total)+' matric. · '+(s.pctReprobado!=null?fmt2(s.pctReprobado)+'% reprob.':'sin datos')),
    ]);
    dropdownMenu.appendChild(item);
  });
  if(!any) dropdownMenu.appendChild(el('div',{class:'empty-note'},'Ninguna carrera coincide con la búsqueda.'));
}
function syncSelectorPlaceholder(){
  selSearch.placeholder = F.carrera!=null ? 'Carrera actual: '+DATA.dict.carrera[F.carrera]+' — clic para cambiar' : 'Buscar carrera...';
}
selSearch.addEventListener('focus', openDropdown);
selSearch.addEventListener('input', openDropdown);
document.addEventListener('click', e=>{ if(!comboWrap.contains(e.target)) closeDropdown(); });

function detalleParalelosCard(rows){
  const card = el('div',{class:'card'});
  card.appendChild(el('h2',null,[iconBadge('list'),'Detalle por asignatura y docente']));
  card.appendChild(el('p',{class:'caption'},'Nivel más fino de análisis dentro de la carrera: cada combinación asignatura + docente. Clic en una fila para filtrar por ambos.'));
  const grouped = groupBy(rows, r=>r[R.ASIG]+'|'+r[R.DOC]);
  let list = [...grouped.entries()].map(([key,agg])=>{
    const [a,d] = key.split('|').map(Number);
    return {a, d, ...aggStats(agg)};
  });
  list.sort((a,b)=>(b.pctReprobado??-1)-(a.pctReprobado??-1));
  if(isPrinting() && (F.asignatura!=null || F.docente!=null)){
    list = list.filter(x=>(F.asignatura==null || x.a===F.asignatura) && (F.docente==null || x.d===F.docente));
  }
  if(!list.length){ card.appendChild(el('div',{class:'empty-note'},'Sin datos para esta carrera con el filtro actual.')); return card; }
  const tableWrap = el('div',{class:'table-scroll'});
  const table = el('table',{class:'datatable'});
  table.appendChild(el('tr',null,[el('th',null,'Asignatura'),el('th',null,'Docente'),el('th',null,'N° evaluados'),el('th',null,'% Aprobado'),el('th',null,'% Reprobado')]));
  list.forEach(x=>{
    const isSel = F.asignatura===x.a && F.docente===x.d;
    const tr = el('tr',{class:'clickable'+(isSel?' selected':''), onclick:()=>{
      const same = F.asignatura===x.a && F.docente===x.d;
      F.asignatura = same? null : x.a;
      F.docente = same? null : x.d;
      rerender();
    }});
    tr.appendChild(el('td',null, DATA.dict.asignatura[x.a]));
    tr.appendChild(el('td',null, DATA.dict.docente[x.d]));
    tr.appendChild(el('td',null, x.rindio+' / '+x.total));
    tr.appendChild(el('td',null, x.pctAprobado!=null? el('span',{class:'tag', style:'background:'+riskColor(100-x.pctAprobado)}, fmt2(x.pctAprobado)+'%'):'—'));
    tr.appendChild(el('td',null, x.pctReprobado!=null? el('span',{class:'tag', style:'background:'+riskColor(x.pctReprobado)}, fmt2(x.pctReprobado)+'%'):'—'));
    table.appendChild(tr);
  });
  tableWrap.appendChild(table);
  card.appendChild(tableWrap);
  return card;
}

function renderCarreraTab(){
  syncSelectorPlaceholder();
  carreraBody.innerHTML = '';
  if(F.carrera==null){
    carreraBody.appendChild(el('div',{class:'empty-note'},'Buscá una carrera arriba para ver su detalle (o hacé clic en una fila de "Resultado por Carrera" en la Vista General).'));
    return;
  }
  const cIdx = F.carrera;
  const rows = filteredRows(new Set(['carrera'])).filter(r=>r[R.CARRERA]===cIdx);
  const agg = emptyAgg(); rows.forEach(r=>addRow(agg,r));
  const s = aggStats(agg);

  carreraBody.appendChild(el('div',{class:'print-section-banner'},'2. Detalle por Carrera: '+DATA.dict.carrera[cIdx]));
  carreraBody.appendChild(el('div',{class:'callout-row'},[
    el('div',{class:'callout info'},[el('div',{class:'big'}, DATA.dict.carrera[cIdx]), el('div',{class:'txt'}, DATA.dict.carreraModalidad[cIdx])]),
  ]));

  carreraBody.appendChild(kpiRow([
    {label:'Matriculados', icon:'clipboard', value: fmtInt(s.total)},
    {label:'% Rindió examen', icon:'check', value: s.pctRindio!=null?fmt2(s.pctRindio)+'%':'—', sub: fmtInt(s.rindio)+' de '+fmtInt(s.total)},
    {label:'% Aprobado', icon:'award', value: s.pctAprobado!=null?fmt2(s.pctAprobado)+'%':'—'},
    {label:'% Reprobado', icon:'alert', value: s.pctReprobado!=null?fmt2(s.pctReprobado)+'%':'—'},
  ]));
  carreraBody.appendChild(kpiRow([
    {label:'Promedio nota final (rindieron)', icon:'trending', value: s.notaProm!=null?fmt1(s.notaProm):'—'},
    {label:'% no realizó examen', icon:'alert', value: s.pctNorindio!=null?fmt2(s.pctNorindio)+'%':'—', sub: fmtInt(s.norindio)+' matrículas-curso'},
    {label:'Asignaturas', icon:'list', value: new Set(rows.map(r=>r[R.ASIG])).size},
    {label:'Docentes', icon:'users', value: new Set(rows.map(r=>r[R.DOC])).size},
  ]));

  const asigScopeRows = filteredRows(new Set(['carrera','asignatura'])).filter(r=>r[R.CARRERA]===cIdx);
  const paraleloScopeRows = filteredRows(new Set(['carrera','asignatura','docente'])).filter(r=>r[R.CARRERA]===cIdx);

  const grid1 = el('div',{class:'grid-2'});
  grid1.appendChild(heatmap3Card({
    title:'Resultado por Asignatura', iconName:'grid', dim:'asignatura', labelFn:i=>DATA.dict.asignatura[i],
    caption:'Ordenado por % de reprobación. Pasá el cursor sobre una celda para ver cuántos estudiantes fueron evaluados. Clic para filtrar todo el dashboard.',
    rows: asigScopeRows,
  }));
  grid1.appendChild(detalleParalelosCard(paraleloScopeRows));
  carreraBody.appendChild(grid1);

  carreraBody.appendChild(notaHistCard(rows));
}

/* ---------- render dispatcher + tabs ---------- */
function rerender(){
  renderFilterBar();
  renderGlobal();
  renderCarreraTab();
}
document.querySelectorAll('.tab-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v=>v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-'+btn.dataset.view).classList.add('active');
  });
});

rerender();
