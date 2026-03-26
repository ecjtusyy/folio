'use client';
import React,{useEffect,useRef,useState} from 'react';
import { apiFetch } from '@/lib/api';
declare global { interface Window { DocsAPI?: any } }

function load(src:string):Promise<void>{
  return new Promise((resolve,reject)=>{
    if(window.DocsAPI) return resolve();
    const s=document.createElement('script');
    s.src=src; s.async=true; s.onload=()=>resolve(); s.onerror=()=>reject(new Error('load onlyoffice api failed'));
    document.body.appendChild(s);
  });
}

export default function Docx({params}:{params:{id:string}}){
  const [err,setErr]=useState<string|null>(null);
  const ed=useRef<any>(null);
  useEffect(()=>{ (async ()=>{
    setErr(null);
    await load('/onlyoffice/web-apps/apps/api/documents/api.js');
    const res=await apiFetch(`/api/onlyoffice/document-url/${params.id}`);
    if(res.status===401||res.status===403){ setErr('private: please login'); return; }
    if(!res.ok){ setErr(`get url failed ${res.status}`); return; }
    const j=await res.json();
    const url=j.document_url;
    if(ed.current?.destroyEditor) try{ ed.current.destroyEditor(); }catch{}
    const cfg={
      document:{fileType:'docx',key:params.id,title:`docx-${params.id}.docx`,url,permissions:{edit:false}},
      documentType:'word',
      editorConfig:{mode:'view',lang:'zh'},
      height:'100%',width:'100%',type:'embedded'
    };
    ed.current=new window.DocsAPI.DocEditor('docx-editor', cfg);
  })().catch(e=>setErr(e?.message||'init failed'));
  return ()=>{ if(ed.current?.destroyEditor) try{ ed.current.destroyEditor(); }catch{} };
  },[params.id]);

  if(err) return <div className="card"><p>❌ {err}</p></div>;
  return <div className="card" style={{width:'100%',height:'85vh'}}><div id="docx-editor" style={{width:'100%',height:'100%'}}/></div>;
}
