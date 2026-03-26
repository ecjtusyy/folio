'use client';
import React,{useEffect,useMemo,useRef,useState} from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch, apiJson } from '@/lib/api';
import { MarkdownEditor } from '@/components/MarkdownEditor';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';

type Note={id:string;title:string;content_md:string;created_at:string;updated_at:string};

export default function Notes(){
  const router=useRouter();
  const [notes,setNotes]=useState<Note[]>([]);
  const [cur,setCur]=useState<string|null>(null);
  const current=useMemo(()=>notes.find(n=>n.id===cur)||null,[notes,cur]);
  const [title,setTitle]=useState('');
  const [content,setContent]=useState('');
  const [preview,setPreview]=useState('');
  const saveT=useRef<any>(null);
  const prevT=useRef<any>(null);

  async function load(){
    try{
      const list=await apiJson<Note[]>('/api/notes');
      setNotes(list);
      if(!cur && list.length) setCur(list[0].id);
    }catch{
      router.push('/login');
    }
  }
  useEffect(()=>{ load(); },[]);
  useEffect(()=>{
    if(current){ setTitle(current.title); setContent(current.content_md); setPreview(current.content_md); }
  },[cur]);

  useEffect(()=>{
    if(prevT.current) clearTimeout(prevT.current);
    prevT.current=setTimeout(()=>setPreview(content),300);
  },[content]);

  useEffect(()=>{
    if(!current) return;
    if(saveT.current) clearTimeout(saveT.current);
    saveT.current=setTimeout(async ()=>{
      await apiFetch(`/api/notes/${current.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,content_md:content})});
      await load();
    },800);
  },[title,content,cur]);

  async function create(){
    const res=await apiFetch('/api/notes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:'Untitled',content_md:''})});
    if(!res.ok){ router.push('/login'); return; }
    const n=await res.json() as Note;
    setNotes(prev=>[n,...prev]); setCur(n.id);
  }
  async function del(id:string){
    if(!confirm('Delete?')) return;
    await apiFetch(`/api/notes/${id}`,{method:'DELETE'});
    setNotes(prev=>prev.filter(n=>n.id!==id));
    setCur(null);
  }
  async function uploadImage(f:File){
    const fd=new FormData();
    fd.append('file',f);
    fd.append('owner_scope','private');
    fd.append('kind','image');
    const res=await apiFetch('/api/files/upload',{method:'POST',body:fd});
    if(!res.ok) throw new Error('upload failed');
    const j=await res.json() as any;
    return j.download_url as string;
  }

  return <div>
    <h1>Notes</h1>
    <button onClick={create}>New Note</button>
    <div style={{display:'grid',gridTemplateColumns:'260px 1fr',gap:12,marginTop:12}}>
      <div className="card">
        <b>My Notes</b>
        <ul>
          {notes.map(n=><li key={n.id} style={{marginBottom:6}}>
            <button onClick={()=>setCur(n.id)} style={{fontWeight:n.id===cur?'bold':'normal'}}>{n.title}</button>
            <button onClick={()=>del(n.id)} style={{marginLeft:8}}>🗑</button>
          </li>)}
        </ul>
      </div>
      {current ? <div>
        <div className="card" style={{marginBottom:12}}>
          <label>Title: <input style={{width:'70%'}} value={title} onChange={e=>setTitle(e.target.value)} /></label>
        </div>
        <div className="split">
          <MarkdownEditor value={content} onChange={setContent} onUploadImage={uploadImage} />
          <MarkdownRenderer markdown={preview} />
        </div>
      </div> : <div className="card">Select a note.</div>}
    </div>
  </div>;
}
