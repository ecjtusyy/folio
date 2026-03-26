'use client';
import React,{useEffect,useState} from 'react';
import { apiFetch, apiJson } from '@/lib/api';
import { MarkdownEditor } from '@/components/MarkdownEditor';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';
import { useRouter } from 'next/navigation';

export default function AdminPosts(){
  const r=useRouter();
  const [list,setList]=useState<any[]>([]);
  const [cur,setCur]=useState<any|null>(null);
  const [title,setTitle]=useState(''); const [slug,setSlug]=useState('');
  const [summary,setSummary]=useState(''); const [tags,setTags]=useState('');
  const [content,setContent]=useState(''); const [preview,setPreview]=useState('');

  async function load(){
    const me=await apiFetch('/api/auth/me');
    const j=await me.json();
    if(!j.authenticated){ r.push('/login'); return; }
    const ps=await apiJson<any[]>('/api/posts');
    setList(ps);
    if(ps.length) setCur(ps[0]);
  }
  useEffect(()=>{ load(); },[]);
  useEffect(()=>{
    if(!cur) return;
    setTitle(cur.title); setSlug(cur.slug); setSummary(cur.summary||''); setContent(cur.content_md||'');
    setPreview(cur.content_md||'');
    setTags(Array.isArray(cur.tags)?cur.tags.join(','):'');
  },[cur?.id]);

  useEffect(()=>{ const t=setTimeout(()=>setPreview(content),300); return ()=>clearTimeout(t); },[content]);

  async function uploadImage(f:File){
    const fd=new FormData();
    fd.append('file',f); fd.append('owner_scope','public'); fd.append('kind','image');
    const res=await apiFetch('/api/files/upload',{method:'POST',body:fd});
    if(!res.ok) throw new Error('upload failed');
    const j=await res.json();
    return j.download_url as string;
  }

  async function save(){
    const tagArr=tags.split(',').map(s=>s.trim()).filter(Boolean);
    if(cur){
      const res=await apiFetch(`/api/posts/${cur.id}`,{method:'PUT',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({title,slug,summary,content_md:content,tags:tagArr})});
      if(!res.ok){ alert('save failed'); return; }
      await load();
    }else{
      const res=await apiFetch('/api/posts',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({title,slug,summary,content_md:content,tags:tagArr,status:'draft'})});
      if(!res.ok){ alert('create failed'); return; }
      await load();
    }
  }

  async function publish(){
    if(!cur) return;
    await apiFetch(`/api/posts/${cur.id}/publish`,{method:'POST'}); await load();
  }
  async function unpublish(){
    if(!cur) return;
    await apiFetch(`/api/posts/${cur.id}/unpublish`,{method:'POST'}); await load();
  }
  async function del(){
    if(!cur) return;
    if(!confirm('Delete?')) return;
    await apiFetch(`/api/posts/${cur.id}`,{method:'DELETE'}); await load();
  }
  function newPost(){
    setCur(null);
    setTitle(''); setSlug(''); setSummary(''); setTags('');
    setContent('# New Post\n\nMath: $E=mc^2$\n'); 
  }

  return <div>
    <h1>Admin Posts</h1>
    <div style={{display:'flex',gap:8}}>
      <button onClick={newPost}>New</button>
      <button onClick={save}>Save</button>
      {cur?.status==='published'?<button onClick={unpublish}>Unpublish</button>:<button onClick={publish}>Publish</button>}
      {cur?<button onClick={del}>Delete</button>:null}
    </div>
    <div style={{display:'grid',gridTemplateColumns:'320px 1fr',gap:12,marginTop:12}}>
      <div className="card">
        <b>All</b>
        <ul>
          {list.map(p=><li key={p.id} style={{marginBottom:8}}>
            <button onClick={()=>setCur(p)} style={{fontWeight:cur?.id===p.id?'bold':'normal'}}>{p.title}</button>
            <div style={{opacity:.7}}>{p.slug} ({p.status})</div>
          </li>)}
        </ul>
      </div>
      <div>
        <div className="card" style={{marginBottom:12}}>
          <label>Title <input style={{width:'100%'}} value={title} onChange={e=>setTitle(e.target.value)} /></label>
          <label>Slug <input style={{width:'100%'}} value={slug} onChange={e=>setSlug(e.target.value)} /></label>
          <label>Summary <input style={{width:'100%'}} value={summary} onChange={e=>setSummary(e.target.value)} /></label>
          <label>Tags <input style={{width:'100%'}} value={tags} onChange={e=>setTags(e.target.value)} /></label>
          <div>Status: {cur?cur.status:'draft(new)'}</div>
        </div>
        <div className="split">
          <MarkdownEditor value={content} onChange={setContent} onUploadImage={uploadImage} />
          <MarkdownRenderer markdown={preview} />
        </div>
      </div>
    </div>
  </div>;
}
