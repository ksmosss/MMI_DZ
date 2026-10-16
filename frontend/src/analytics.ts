declare global { interface Window { ym?: (...args:unknown[])=>void } }
const id=Number(import.meta.env.VITE_METRIKA_ID || 0);
export function trackEvent(name:string){if(id && window.ym)window.ym(id,'reachGoal',name)}
export function initAnalytics(){
 if(!id || !Number.isInteger(id) || id<1)return;
 if(!window.ym){
   const queued= function(...args:unknown[]){(queued as typeof queued & {a: unknown[][]}).a.push(args)} as typeof window.ym & {a:unknown[][];l?:number};
   queued.a=[]; queued.l=Date.now(); window.ym=queued;
 }
 const src=`https://mc.yandex.ru/metrika/tag.js`;
 if(!document.querySelector(`script[src="${src}"]`)){
   const script=document.createElement('script');script.async=true;script.src=src;document.head.appendChild(script);
 }
 window.ym(id,'init',{clickmap:true,trackLinks:true,accurateTrackBounce:true});
}
