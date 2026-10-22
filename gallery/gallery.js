(()=>{
 'use strict';
 const meta={
  SCC:{name:'Semantic Coverage & Consistency',suite:'composition',short:'Semantic coverage'},RGC:{name:'Relational Graph Consistency',suite:'composition',short:'Relational graph'},LAC:{name:'Layout Arrangement Consistency',suite:'composition',short:'Layout arrangement'},
  GAC:{name:'Global Appearance Conditioning',suite:'appearance',short:'Global appearance'},LAB:{name:'Local Appearance Binding',suite:'appearance',short:'Local appearance'},AHC:{name:'Appearance Harmonization & Coherence',suite:'appearance',short:'Appearance harmony'},
  SEL:{name:'Selection & Retrieval',suite:'reasoning',short:'Selection & retrieval'},TSR:{name:'Temporal / State Reasoning',suite:'reasoning',short:'Temporal / state'},AGG:{name:'Counting & Aggregation',suite:'reasoning',short:'Counting & aggregation'}
 };
 const suiteNames={composition:'Scene Composition',appearance:'Visual Appearance',reasoning:'Reference Reasoning'};
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const src=p=>'./visual-data/'+String(p).replace(/^\/visual-data\//,'');
 const grid=document.querySelector('#case-grid'),status=document.querySelector('#gallery-status'),dialog=document.querySelector('#case-dialog'),targetDialog=document.querySelector('#target-dialog'),search=document.querySelector('#case-search'),reset=document.querySelector('#reset-filters'),loadMore=document.querySelector('#load-more');
 const params=new URLSearchParams(location.search);
 let cases=[],suite='all',category=meta[params.get('category')]?params.get('category'):'all',query=params.get('q')||'',limit=18,selected=null,returnFocus=null;
 if(category!=='all')suite=meta[category].suite;
 search.value=query;
 function records(){const needle=query.trim().toLowerCase();return cases.filter(c=>(suite==='all'||meta[c.category].suite===suite)&&(category==='all'||c.category===category)&&(!needle||[c.id,meta[c.category].name,suiteNames[meta[c.category].suite],c.prompt].join(' ').toLowerCase().includes(needle)))}
 function updateUrl(){const p=new URLSearchParams();if(category!=='all')p.set('category',category);else if(suite!=='all')p.set('suite',suite);if(query)p.set('q',query);if(selected)p.set('case',selected);history.replaceState(null,'',location.pathname+(p.size?'?'+p:'')+location.hash)}
 function renderFilters(){
  document.querySelectorAll('[data-suite]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.suite===suite)));
  const codes=Object.keys(meta).filter(code=>suite==='all'||meta[code].suite===suite);
  document.querySelector('#category-filters').innerHTML='<button type="button" data-category="all" aria-pressed="'+(category==='all')+'">All categories</button>'+codes.map(code=>'<button type="button" data-category="'+code+'" aria-pressed="'+(category===code)+'" title="'+esc(meta[code].name)+'" aria-label="'+esc(code+': '+meta[code].name)+'"><b>'+code+'</b><span class="chip-label">'+esc(meta[code].short)+'</span></button>').join('');
 }
 function render(){
  const list=records(),shown=list.slice(0,limit);
  document.querySelector('#case-count').textContent=list.length;
  reset.hidden=suite==='all'&&category==='all'&&!query;
  renderFilters();
  grid.hidden=!list.length;status.hidden=!!list.length;
  if(!list.length)status.innerHTML='<strong>No matching cases</strong><p>Try another keyword or clear the active filters.</p><button type="button" class="button" data-reset>Show all cases ↗</button>';
  grid.innerHTML=shown.map((c,i)=>'<article class="case-card"><button class="card-open" type="button" data-case="'+c.id+'" aria-label="Open '+c.id+': '+esc(meta[c.category].name)+'"><div class="card-visual"><img src="'+esc(src(c.simulatedTarget))+'" alt="Simulated target for '+c.id+'" loading="'+(i<6?'eager':'lazy')+'" decoding="async"><span class="card-ref-count"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6" y="6" width="15" height="15" rx="2"/><path d="M3 17V5a2 2 0 0 1 2-2h12m-8 14 3-3 3 3 3-5 3 5"/></svg>'+c.references.length+' refs</span></div><div class="card-copy"><div class="card-category"><span>'+suiteNames[meta[c.category].suite]+'</span><span class="category-code">'+c.category+'</span></div><h2>'+esc(meta[c.category].name)+'</h2><p class="card-id">'+c.id+'</p><p class="card-prompt">'+esc(c.prompt)+'</p><div class="card-bottom"><span>Explore case</span><span aria-hidden="true">↗</span></div></div></button></article>').join('');
  document.querySelector('#shown-count').textContent=list.length?'Showing '+shown.length+' of '+list.length+' cases':'';
  loadMore.hidden=shown.length>=list.length;
  updateUrl();
 }
 function clear(){suite='all';category='all';query='';search.value='';limit=18;render()}
 function openCase(id){
  const c=cases.find(c=>c.id===id);if(!c)return;
  if(!dialog.open)returnFocus=document.activeElement;
  selected=id;const m=meta[c.category],list=records(),position=list.findIndex(c=>c.id===id);
  dialog.innerHTML='<header class="case-header"><div><p><span class="category-code">'+c.category+'</span>'+suiteNames[m.suite]+'</p><h2 id="case-title">'+esc(m.name)+'</h2><div class="case-id">'+c.id+'</div></div><div class="modal-controls"><button type="button" data-move="-1" aria-label="Previous case">←</button><span>'+((position>=0?position:cases.indexOf(c))+1)+' / '+(position>=0?list.length:cases.length)+'</span><button type="button" data-move="1" aria-label="Next case">→</button><button type="button" class="close-dialog" data-close aria-label="Close case details" autofocus>×</button></div></header><div class="case-body"><div class="case-overview"><button type="button" class="target-panel" data-target aria-label="Enlarge simulated target for '+c.id+'"><img src="'+esc(src(c.simulatedTarget))+'" alt="Simulated target for '+c.id+'"><span><b>Simulated target</b> View image ↗</span></button><section class="instruction-panel" aria-labelledby="instruction-title"><p class="eyebrow" id="instruction-title">Synthesis instruction</p><div class="instruction-content" tabindex="0">'+esc(c.prompt)+'</div></section></div><section aria-labelledby="references-title"><div class="reference-heading"><h3 id="references-title">Reference images <span>'+c.references.length+'</span></h3><p>The complete visual context for this case</p></div><div class="reference-grid">'+c.references.map((p,i)=>'<div class="reference-item"><img src="'+esc(src(p))+'" alt="'+c.id+' reference '+(i+1)+'" loading="lazy" decoding="async"><span>'+String(i+1).padStart(2,'0')+'</span></div>').join('')+'</div></section><p class="case-footnote">The simulated target illustrates the intended scene. Reference images are shown as preview thumbnails.</p></div>';
  if(!dialog.open)dialog.showModal();
  dialog.scrollTop=0;dialog.querySelector('[data-close]').focus();updateUrl();
 }
 function closeCase(){dialog.close()}
 function move(direction){const list=records(),pool=list.some(c=>c.id===selected)?list:cases;const i=pool.findIndex(c=>c.id===selected);if(pool.length)openCase(pool[(i+direction+pool.length)%pool.length].id)}
 function previewTarget(){const c=cases.find(c=>c.id===selected);targetDialog.innerHTML='<div class="target-preview-header"><span>'+c.id+' · Simulated target</span><button type="button" data-close-target aria-label="Close target preview" autofocus>×</button></div><img src="'+esc(src(c.simulatedTarget))+'" alt="Simulated target for '+c.id+'">';targetDialog.showModal()}
 document.querySelectorAll('[data-suite]').forEach(b=>b.addEventListener('click',()=>{suite=b.dataset.suite;category='all';limit=18;render()}));
 document.querySelector('#category-filters').addEventListener('click',e=>{const b=e.target.closest('[data-category]');if(b){category=b.dataset.category;limit=18;render()}});
 search.addEventListener('input',()=>{query=search.value;limit=18;render()});
 reset.addEventListener('click',clear);status.addEventListener('click',e=>{if(e.target.closest('[data-reset]'))clear()});
 loadMore.addEventListener('click',()=>{limit+=18;render()});
 grid.addEventListener('click',e=>{const b=e.target.closest('[data-case]');if(b)openCase(b.dataset.case)});
 dialog.addEventListener('click',e=>{if(e.target.closest('[data-close]'))closeCase();if(e.target.closest('[data-move]'))move(Number(e.target.closest('[data-move]').dataset.move));if(e.target.closest('[data-target]'))previewTarget();if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)closeCase()}});
 dialog.addEventListener('close',()=>{selected=null;updateUrl();if(returnFocus?.isConnected)returnFocus.focus()});
 targetDialog.addEventListener('click',e=>{if(e.target.closest('[data-close-target]')||e.target===targetDialog)targetDialog.close()});
 document.addEventListener('keydown',e=>{if(!dialog.open||targetDialog.open||e.target.closest('.instruction-content'))return;if(e.key==='ArrowLeft'){e.preventDefault();move(-1)}if(e.key==='ArrowRight'){e.preventDefault();move(1)}});
 const requestedCase=params.get('case');
 if(!meta[params.get('category')]&&suiteNames[params.get('suite')])suite=params.get('suite');
 fetch('./visual-data/cases.json').then(r=>{if(!r.ok)throw new Error('The case index could not be loaded.');return r.json()}).then(data=>{cases=data.cases;render();if(requestedCase)openCase(requestedCase)}).catch(()=>{status.hidden=false;status.innerHTML='<strong>Unable to load the gallery</strong><p>Please reload this page to try again.</p>';document.querySelector('#case-count').textContent='—'});
})();
