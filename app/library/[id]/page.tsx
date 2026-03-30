'use client';
import React,{useEffect,useState} from 'react';
import Link from 'next/link';
import { apiFetch } from '@/lib/api';
import { MarkdownRenderer } from '@/components/MarkdownRenderer';

export default function Library({params}:{params:{id:string}}){
  const [item,setItem]=useState<any|null>(null);
  const [err,setErr]=useState<string|null>(null);
  useEffect(()=>{ (async ()=>{
    const res=await apiFetch(`/api/library/${params.id}`);
    if(res.status===401||res.status===403){ setErr('private: please login'); return; }
    if(!res.ok){ setErr(`load failed ${res.status}`); return; }
    setItem(await res.json());
  })(); },[params.id]);
  if(err) return <div className="card"><p>❌ {err}</p><Link href="/login">login</Link></div>;
  if(!item) return <div className="card">Loading...</div>;
  return <div>
    <h1>{item.title}</h1>
    {item.type==='md'? <MarkdownRenderer markdown={item.content_md||''} />: null}
    {item.type==='docx'? <div className="card"><iframe src={`/viewer/docx/${item.source_file_id}`} style={{width:'100%',height:'80vh',border:0}}/></div>:null}
    {item.type==='tex' && item.rendered_file_id? <div className="card"><iframe src={`/viewer/pdf/${item.rendered_file_id}`} style={{width:'100%',height:'80vh',border:0}}/></div>:null}
  </div>;
}
