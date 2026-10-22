(()=>{
 'use strict';
 const table=document.querySelector('#leaderboard-table');
 let dataset='strategy',sortKey='overall.overall',descending=true;
 const columns=[{name:'Method',key:'info.name',text:true},{name:'Family',key:'info.typeLabel',text:true},{name:'Avg.',key:'overall.overall'},{name:'P@70%',key:'overall.p70'},{name:'Scene Composition',key:'topo.overall'},{name:'Visual Appearance',key:'appr.overall'},{name:'Reference Reasoning',key:'reason.overall'}];
 const detailColumns=[{name:'SCC',key:'topo.scc'},{name:'RGC',key:'topo.rgc'},{name:'LAC',key:'topo.lac'},{name:'GAC',key:'appr.gac'},{name:'LAB',key:'appr.lab'},{name:'AHC',key:'appr.ahc'},{name:'SEL',key:'reason.sel'},{name:'TSR',key:'reason.tsr'},{name:'AGG',key:'reason.agg'}];
 const value=(row,key)=>key.split('.').reduce((a,k)=>a?.[k],row);
 function render(){
  const ds=window.LB.datasets[dataset];
  const cols=document.querySelector('#show-details').checked?columns.concat(detailColumns):columns;
  const rows=[...ds.rows].sort((a,b)=>{const av=value(a,sortKey),bv=value(b,sortKey);return(typeof av==='string'?av.localeCompare(bv):av-bv)*(descending?-1:1)});
  document.querySelector('#table-context').textContent=dataset==='strategy'?'Nano Banana 2 fixed as image generator · 8 generation conditions':'OpenClaw + RPR fixed as controller · 3 image generators';
  table.innerHTML='<thead><tr>'+cols.map(c=>'<th scope="col"'+(sortKey===c.key?' aria-sort="'+(descending?'descending':'ascending')+'"':'')+'><button type="button" data-sort="'+c.key+'">'+c.name+(sortKey===c.key?(descending?' ↓':' ↑'):'')+'</button></th>').join('')+'</tr></thead><tbody>'+rows.map((row,index)=>'<tr>'+cols.map((c,i)=>{
   const v=value(row,c.key);
   if(i===0)return '<td><span class="rank-number">'+String(index+1).padStart(2,'0')+'</span><span class="row-name">'+v+'</span></td>';
   if(c.text)return '<td><span class="type-tag">'+v+'</span></td>';
   const best=Math.max(...ds.rows.map(r=>value(r,c.key)));
   return '<td><span class="'+(v===best?'best':'')+'">'+v.toFixed(1)+'</span>'+(c.key==='overall.overall'?'<span class="score-bar"><i style="width:'+v+'%"></i></span>':'')+'</td>';
  }).join('')+'</tr>').join('')+'</tbody>';
 }
 document.querySelectorAll('[data-dataset]').forEach(btn=>btn.addEventListener('click',()=>{dataset=btn.dataset.dataset;sortKey='overall.overall';descending=true;document.querySelectorAll('[data-dataset]').forEach(b=>b.setAttribute('aria-selected',String(b===btn)));render()}));
 document.querySelector('#show-details').addEventListener('change',render);
 table.addEventListener('click',event=>{const btn=event.target.closest('[data-sort]');if(!btn)return;descending=sortKey===btn.dataset.sort?!descending:!btn.dataset.sort.startsWith('info.');sortKey=btn.dataset.sort;render()});
 const marquee=document.querySelector('.institution-marquee');
 const group=marquee.querySelector('.institution-group');
 const duplicate=group.cloneNode(true);
 duplicate.setAttribute('aria-hidden','true');
 duplicate.querySelectorAll('a').forEach(a=>a.tabIndex=-1);
 marquee.querySelector('.institution-track').appendChild(duplicate);
 document.querySelector('#marquee-toggle').addEventListener('click',event=>{const paused=marquee.classList.toggle('is-paused');event.currentTarget.setAttribute('aria-pressed',String(paused));event.currentTarget.textContent=paused?'▶ Play':'Ⅱ Pause'});
 const showcase=document.querySelector('.showcase-viewport');
 const cases=showcase.querySelector('.showcase-group');
 const repeatedCases=cases.cloneNode(true);
 repeatedCases.setAttribute('aria-hidden','true');
 repeatedCases.querySelectorAll('a').forEach(a=>a.tabIndex=-1);
 showcase.querySelector('.hero-showcase').appendChild(repeatedCases);
 for(let i=0;i<3;i++){const copy=repeatedCases.cloneNode(true);showcase.querySelector('.hero-showcase').appendChild(copy)}
 const caseTrack=showcase.querySelector('.hero-showcase');
 let caseCards=[...caseTrack.querySelectorAll('.showcase-card')];
 const categoryLabels={SCC:'Semantic coverage & consistency',RGC:'Relational graph consistency',LAC:'Layout arrangement',GAC:'Global appearance',LAB:'Local appearance binding',AHC:'Appearance harmonization',SEL:'Selection & retrieval',TSR:'Temporal / state reasoning',AGG:'Counting & aggregation'};
 fetch('gallery/visual-data/cases.json').then(response=>{if(!response.ok)throw new Error('Case index unavailable');return response.json()}).then(data=>{
  const shuffled=[...data.cases];
  for(let i=shuffled.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[shuffled[i],shuffled[j]]=[shuffled[j],shuffled[i]]}
  const template=cases.querySelector('.showcase-card');
  const cards=shuffled.map(record=>{
   const card=template.cloneNode(true);
   card.href='gallery/?case='+encodeURIComponent(record.id);
   card.querySelector('.mini-window b').textContent=record.id.replace('-',' / ');
   const image=card.querySelector('img');
   image.dataset.src='gallery/visual-data/'+record.simulatedTarget.replace(/^\/visual-data\//,'');
   image.removeAttribute('src');image.alt='Simulated target for '+record.id;image.decoding='async';
   card.querySelector('.showcase-caption strong').textContent=record.id;
   card.querySelector('.showcase-caption span').textContent=categoryLabels[record.category]||record.category;
   return card;
  });
  cases.replaceChildren(...cards);caseTrack.replaceChildren(cases);caseCards=cards;
 }).catch(()=>{document.querySelector('.showcase-note').textContent='Case previews could not be fully loaded. Open the gallery to browse all 90 cases.'});
 const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)');
 let casePhase=0,lastFrame=0,dragStart=null,dragged=false;
 showcase.addEventListener('pointerdown',event=>{if(event.button!==0)return;dragStart={x:event.clientX,phase:casePhase};dragged=false});
 window.addEventListener('pointermove',event=>{if(!dragStart)return;const delta=event.clientX-dragStart.x;if(Math.abs(delta)>6)dragged=true;casePhase=dragStart.phase+delta/Math.max(showcase.clientWidth,800)});
 window.addEventListener('pointerup',()=>{dragStart=null});
 showcase.addEventListener('dragstart',event=>event.preventDefault());
 showcase.addEventListener('click',event=>{if(dragged){event.preventDefault();dragged=false}},true);
 function moveCases(now){
  const elapsed=lastFrame?Math.min(now-lastFrame,50):0;lastFrame=now;
  if(!reducedMotion.matches){
   const width=showcase.clientWidth,cardWidth=caseCards[0].offsetWidth;
   const radiusX=Math.max(width,800),radiusY=radiusX*.556;
   // Match the original static showcase gaps at its responsive breakpoints.
   const gap=width<=700?14:width<=1000?15:22;
   const angleStep=(cardWidth+gap)/radiusX,cycle=caseCards.length*angleStep;
   const paused=dragStart||showcase.matches(':hover,:focus-within')||showcase.classList.contains('is-paused');
   if(!paused&&!document.hidden)casePhase=(casePhase-elapsed*.000018)%cycle;
   caseTrack.style.height=(caseCards[0].offsetHeight+110)+'px';
   caseCards.forEach((card,index)=>{
    const angle=((index*angleStep+casePhase+cycle/2)%cycle+cycle)%cycle-cycle/2;
    const x=width/2+radiusX*Math.sin(angle)-cardWidth/2;
    const visible=Math.abs(angle)<Math.PI/2&&x>-cardWidth-80&&x<width+80;
    card.style.visibility=visible?'visible':'hidden';
    if(!visible)return;
    const image=card.querySelector('img');if(image.dataset.src){image.src=image.dataset.src;delete image.dataset.src}
    const highlighted=card.matches(':hover,:focus-visible');
    const y=18+radiusY*(1-Math.cos(angle))-(highlighted?12:0);
    const rotation=Math.atan2(radiusY*Math.sin(angle),radiusX*Math.cos(angle))*180/Math.PI;
    card.style.transform='translate('+x+'px,'+y+'px) rotate('+(highlighted?0:rotation)+'deg)';
   });
  }else{caseTrack.style.height='';caseCards.forEach(card=>{card.style.transform='';card.style.visibility='';const image=card.querySelector('img');if(image.dataset.src){image.loading='lazy';image.src=image.dataset.src;delete image.dataset.src}})}
  requestAnimationFrame(moveCases);
 }
 requestAnimationFrame(moveCases);
 document.querySelector('#showcase-toggle').addEventListener('click',event=>{const paused=showcase.classList.toggle('is-paused');event.currentTarget.setAttribute('aria-pressed',String(paused));event.currentTarget.textContent=paused?'▶ Play':'Ⅱ Pause'});
 render();
})();
