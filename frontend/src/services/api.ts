const BASE=import.meta.env.VITE_API_URL || 'http://localhost:8000';
export function token(){return localStorage.getItem('universe_token')||''}
export async function api(path:string,init:RequestInit={}){const headers:Record<string,string>={'Content-Type':'application/json',...(init.headers as Record<string,string>||{})};if(token())headers.Authorization=`Bearer ${token()}`;const res=await fetch(BASE+path,{...init,headers});const data=await res.json().catch(()=>({detail:'Unexpected server response'}));if(!res.ok)throw new Error(data.detail||`Request failed (${res.status})`);return data;}
