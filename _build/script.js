<script>
(function(){
  var bar=document.getElementById('bar');
  var saveData=!!(navigator.connection&&navigator.connection.saveData);
  // play(): WebView対策で muted をJS側でも明示してから呼ぶ
  function tryPlay(v){try{v.muted=true;v.defaultMuted=true;var p=v.play();if(p&&p.catch){p.catch(function(){})}}catch(e){}}
  // 公開サーバー経由だと VP9 webm が Chrome でデコードエラーになることがあるため mp4（H.264）だけで配信する
  function addSrc(v,webm,mp4){var b=document.createElement('source');b.src=mp4;b.type='video/mp4';v.appendChild(b);
    v.autoplay=true; v.setAttribute('autoplay','');
    ['loadedmetadata','loadeddata','canplay','canplaythrough'].forEach(function(t){v.addEventListener(t,function(){ if(v.paused&&(v===hv||v.dataset.vis)){tryPlay(v);} });});
    v.load();}
  // hero: スマホもPCと同じ横長版（スマホは横幅に合わせて全体を表示、2026-11-05）
  var hv=document.getElementById('heroVideo'), hp=document.getElementById('heroPoster');
  if(!saveData){
    var base='video/hero8_land';
    addSrc(hv,base+'.webm',base+'.mp4');
    hv.addEventListener('playing',function(){hp.style.transition='opacity 1s';hp.style.opacity='0';},{once:true});
    tryPlay(hv);
  }
  // reveal
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('on');io.unobserve(e.target);}})},{rootMargin:'0px 0px -6% 0px',threshold:0.05});
  document.querySelectorAll('.rv,.zoom').forEach(function(el){io.observe(el)});
  // lazy videos: 1画面手前で読み込み、画面外では停止
  var lio=new IntersectionObserver(function(es){es.forEach(function(e){var v=e.target;
    if(e.isIntersecting){ v.dataset.vis='1'; if(!v.dataset.loaded){ if(!saveData){var sp=window.innerWidth<760&&v.dataset.mp4Sp; addSrc(v,sp?v.dataset.webmSp:v.dataset.webm,sp?v.dataset.mp4Sp:v.dataset.mp4);} v.dataset.loaded='1'; } tryPlay(v);
      var n=0; (function retry(){ if(n++<6&&v.dataset.vis&&v.paused){ tryPlay(v); setTimeout(retry,1500);} })(); }
    else{ v.dataset.vis=''; if(v.dataset.loaded){ v.pause(); } }
  })},{rootMargin:'100% 0px 100% 0px',threshold:0.01});
  document.querySelectorAll('video.lazy').forEach(function(v){lio.observe(v)});
  // WeChat内蔵ブラウザ対策: JSBridge準備完了時と最初のタッチ/スクロール時に、画面内の動画を再生し直す
  function kick(){ if(!saveData){ if(hv.paused){tryPlay(hv);} document.querySelectorAll('video.lazy').forEach(function(v){ if(v.dataset.vis&&v.dataset.loaded&&v.paused){tryPlay(v);} }); } }
  if(window.WeixinJSBridge){kick();}else{document.addEventListener('WeixinJSBridgeReady',kick,false);}
  var kt=0; ['touchstart','touchend','click','scroll'].forEach(function(t){window.addEventListener(t,function(){var now=Date.now(); if(now-kt>800){kt=now;kick();}},{passive:true});});
  function onScroll(){bar.classList.toggle('solid',window.scrollY>window.innerHeight*0.7)}
  window.addEventListener('scroll',onScroll,{passive:true});onScroll();
})();
</script>