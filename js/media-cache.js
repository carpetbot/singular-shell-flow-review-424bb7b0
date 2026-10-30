// Optional MP4 cache. Global payload/row bounds include every account.
export const MEDIA_DB='singular-media.v1';
export const MAX_CACHE_BYTES=64*1024*1024, MAX_MEDIA_ROWS=16;
const accountOK=a=>typeof a==='string'&&/^[a-f0-9]{64}$/.test(a);
const jobOK=j=>typeof j==='string'&&/^[A-Za-z0-9_-]{1,160}$/.test(j);
function identity(account,job){if(!accountOK(account)||!jobOK(job))throw new Error('Invalid media cache identity');return account+':'+job;}
function database(){return new Promise((resolve,reject)=>{
  const r=indexedDB.open(MEDIA_DB,1);let expired=false;
  const timer=setTimeout(()=>{expired=true;reject(new Error('Media cache unavailable'));},3000);
  r.onupgradeneeded=()=>r.result.createObjectStore('media',{keyPath:'id'});
  r.onerror=r.onblocked=()=>{expired=true;clearTimeout(timer);reject(new Error('Media cache unavailable'));};
  r.onsuccess=()=>{clearTimeout(timer);if(expired){r.result.close();return;}r.result.onversionchange=()=>r.result.close();resolve(r.result);};
});}
export async function readMedia(account,job){
  const id=identity(account,job),db=await database();
  try{return await new Promise((resolve,reject)=>{
    const t=db.transaction('media'),r=t.objectStore('media').get(id);let row;
    r.onsuccess=()=>{row=r.result;};
    t.oncomplete=()=>resolve(row?.account===account&&row.job===job&&row.blob instanceof Blob&&row.blob.type==='video/mp4'&&row.blob.size>0&&row.blob.size<=MAX_CACHE_BYTES?row.blob:null);
    t.onerror=t.onabort=()=>reject(new Error('Media cache read failed'));
  });}finally{db.close();}
}
export async function saveMedia(account,job,blob){
  const id=identity(account,job);
  if(!(blob instanceof Blob)||blob.type!=='video/mp4'||!blob.size||blob.size>MAX_CACHE_BYTES)return false;
  const db=await database();
  try{await new Promise((resolve,reject)=>{
    const t=db.transaction('media','readwrite'),s=t.objectStore('media'),r=s.getAll();
    r.onsuccess=()=>{
      // Never trust stored byte counters; count actual blobs inside the write lock.
      const rows=r.result.filter(x=>x.id!==id);
      rows.sort((a,b)=>a.created_at-b.created_at||String(a.id).localeCompare(String(b.id)));
      let bytes=blob.size+rows.reduce((n,x)=>n+(x.blob instanceof Blob?x.blob.size:MAX_CACHE_BYTES),0),count=rows.length+1;
      for(const old of rows){if(bytes<=MAX_CACHE_BYTES&&count<=MAX_MEDIA_ROWS)break;s.delete(old.id);bytes-=old.blob instanceof Blob?old.blob.size:MAX_CACHE_BYTES;count--;}
      s.put({id,account,job,blob,created_at:Date.now()});
    };
    t.oncomplete=resolve;t.onerror=t.onabort=()=>reject(new Error('Media cache write failed'));
  });return true;}finally{db.close();}
}
