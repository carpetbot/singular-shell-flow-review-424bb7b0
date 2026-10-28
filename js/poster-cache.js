// Optional, bounded posters only. No credentials or video bytes enter this database.
export const MAX_POSTER_BYTES=128*1024, MAX_CACHE_BYTES=2*1024*1024, MAX_POSTERS=64;
const safeAccount=a=>typeof a==='string'&&/^[a-f0-9]{64}$/.test(a);
const safeJob=id=>typeof id==='string'&&/^[A-Za-z0-9_-]{1,160}$/.test(id);
const safeImage=s=>typeof s==='string'&&s.length<=MAX_POSTER_BYTES&&/^data:image\/jpeg;base64,[A-Za-z0-9+/]+={0,2}$/.test(s);
async function database(){
  return new Promise((resolve,reject)=>{
    const r=indexedDB.open('singular-posters.v1',1);
    r.onupgradeneeded=()=>r.result.createObjectStore('posters',{keyPath:'id'});
    r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
    r.onblocked=()=>reject(new Error('Poster cache unavailable'));
  });
}
export async function readPosters(account){
  if(!safeAccount(account))throw new Error('Invalid poster account');
  const db=await database();
  try{return await new Promise((resolve,reject)=>{
    const t=db.transaction('posters'),r=t.objectStore('posters').getAll();let rows=[];
    r.onsuccess=()=>{rows=r.result;};t.oncomplete=()=>resolve(new Map(rows.filter(x=>x.account===account&&safeJob(x.job)&&safeImage(x.image)).map(x=>[x.job,x.image])));
    t.onabort=t.onerror=()=>reject(t.error);
  });}finally{db.close();}
}
export async function savePoster(account,job,image){
  if(!safeAccount(account)||!safeJob(job)||!safeImage(image))throw new Error('Invalid poster');
  const db=await database();
  try{await new Promise((resolve,reject)=>{
    const t=db.transaction('posters','readwrite'),s=t.objectStore('posters'),r=s.getAll();
    r.onsuccess=()=>{
      const row={id:account+':'+job,account,job,image,created_at:Date.now()};
      const rows=r.result.filter(x=>x.id!==row.id);rows.push(row);
      rows.sort((a,b)=>a.created_at-b.created_at||a.id.localeCompare(b.id));
      let bytes=rows.reduce((n,x)=>n+(typeof x.image==='string'?x.image.length:MAX_CACHE_BYTES),0),count=rows.length;
      s.put(row);
      for(const old of rows){if(bytes<=MAX_CACHE_BYTES&&count<=MAX_POSTERS)break;s.delete(old.id);bytes-=typeof old.image==='string'?old.image.length:MAX_CACHE_BYTES;count--;}
    };
    t.oncomplete=resolve;t.onabort=t.onerror=()=>reject(t.error);
  });}finally{db.close();}
}
export function capturePoster(player){
  if(player.readyState<2||!player.videoWidth||!player.videoHeight)return null;
  const canvas=document.createElement('canvas'),scale=Math.min(1,320/player.videoWidth);
  canvas.width=Math.max(1,Math.round(player.videoWidth*scale));canvas.height=Math.max(1,Math.round(player.videoHeight*scale));
  try{canvas.getContext('2d').drawImage(player,0,0,canvas.width,canvas.height);const image=canvas.toDataURL('image/jpeg',0.7);return safeImage(image)?image:null;}catch{return null;}
}
