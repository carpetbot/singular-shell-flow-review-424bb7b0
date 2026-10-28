// A1 recovery only: no creation, polling, or durable job/media storage.
import { get } from './store.js';
export const MAX_MEDIA_BYTES = 100 * 1024 * 1024;
const jobId = /^[A-Za-z0-9_-]{1,160}$/;
export async function listVideos(cursor, signal){
  signal = signal ? AbortSignal.any([signal,AbortSignal.timeout(30000)]) : AbortSignal.timeout(30000);
  const key = get().settings.apiKey.trim();
  const q = new URLSearchParams({limit:'50'});
  if(cursor) q.set('cursor', cursor);
  const r = await fetch('/v1/videos?' + q, {headers:{Authorization:'Bearer '+key},signal,cache:'no-store',redirect:'error',credentials:'omit'});
  if(!r.ok) throw new Error(r.status===401 ? 'Key not accepted. Check Settings and retry.' : 'Could not load videos. Retry.');
  const data = await r.json();
  if(!data || !Array.isArray(data.items) || data.items.length>100 || data.items.some(x=>!x || typeof x.id!=='string' || !jobId.test(x.id)) ||
    (data.next_cursor != null && data.next_cursor !== '' && (typeof data.next_cursor!=='string' || !/^[A-Za-z0-9_=-]{1,200}$/.test(data.next_cursor)))) throw new Error('Video list unavailable: unexpected response.');
  return {items:data.items,next_cursor:data.next_cursor || null};
}
export async function fetchVideo(id, signal){
  signal = signal ? AbortSignal.any([signal,AbortSignal.timeout(120000)]) : AbortSignal.timeout(120000);
  if(!jobId.test(id)) throw new Error('Invalid video reference.');
  const key = get().settings.apiKey.trim();
  const r = await fetch('/v1/videos/'+id+'/content', {headers:{Authorization:'Bearer '+key},signal,cache:'no-store',redirect:'error',credentials:'omit'});
  if(!r.ok){ await r.body?.cancel(); throw new Error('Video unavailable. Retry opening it.'); }
  const size = r.headers.get('Content-Length');
  if(size && (!/^\d+$/.test(size) || Number(size)>MAX_MEDIA_BYTES)){await r.body?.cancel();throw new Error('Video exceeds 100 MB.');}
  const reader = r.body.getReader(), chunks=[];let total=0;
  try{
    while(true){
      const {done,value}=await reader.read();if(done) break;
      total+=value.byteLength;
      if(total>MAX_MEDIA_BYTES) throw new Error('Video exceeds 100 MB.');
      chunks.push(value);
    }
    if(size && total!==Number(size)) throw new Error('Incomplete video. Retry opening it.');
    return new Blob(chunks,{type:'video/mp4'});
  }catch(e){await reader.cancel().catch(()=>{});throw e;}
}
