'use client';
import React,{useEffect,useState} from 'react';
import { apiFetch, apiJson } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Imports(){
  const r=useRouter();
  const [items,setItems]=useState<any[]>([]);
  const [file,setFile]=useState<File|null>(null);
  const [visibility,setV]=useState<'private'|'public'>('private');
  const [title,setTitle]=useState('');
  async function load(){
    const me=await apiFetch('/api/auth/me');
    const j=await me.json();
    if(!j.authenticated){ r.push('/login'); return; }
    const list=await apiJson<any[]>('/api/imports');
    setItems(list);
  }
  useEffect(()=>{ load(); },[]);
  async function upload(){
    if(!file) return;
    const fd=new FormData();
    fd.append('file',file);
    fd.append('visibility',visibility);
    if(title) fd.append('title',title);
    const res=await apiFetch('/api/imports',{method:'POST',body:fd});
    if(!res.ok){ alert(await res.text()); return; }
    setFile(null); setTitle(''); await load();
  }
  async function toggle(it:any){
    const next=it.visibility==='public'?'private':'public';
    await apiFetch(`/api/imports/${it.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({visibility:next})});
    await load();
  }
  async function del(it:any){
    if(!confirm('Delete?')) return;
    await apiFetch(`/api/imports/${it.id}`,{method:'DELETE'}); await load();
  }
  return <div>
    <h1>Imports</h1>
    <div className="card">
      <input type="file" onChange={e=>setFile(e.target.files?.[0]||null)} />
      <select value={visibility} onChange={e=>setV(e.target.value as any)}>
        <option value="private">private</option>
        <option value="public">public</option>
      </select>
      <input placeholder="title (optional)" value={title} onChange={e=>setTitle(e.target.value)} />
      <button onClick={upload} disabled={!file}>Upload</button>
    </div>
    <div className="card" style={{marginTop:12}}>
      <ul>
        {items.map(it=><li key={it.id} style={{marginBottom:10}}>
          <b>{it.title}</b> <span style={{opacity:.7}}>({it.type},{it.visibility})</span>
          <div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:4}}>
            <Link href={`/library/${it.id}`}>/library/{it.id}</Link>
            {it.type==='docx'? <Link href={`/viewer/docx/${it.source_file_id}`}>DOCX Viewer</Link>:null}
            {it.type==='tex' && it.rendered_file_id? <Link href={`/viewer/pdf/${it.rendered_file_id}`}>PDF Viewer</Link>:null}
            <button onClick={()=>toggle(it)}>Toggle</button>
            <button onClick={()=>del(it)}>Delete</button>
          </div>
        </li>)}
      </ul>
    </div>
  </div>;
}
