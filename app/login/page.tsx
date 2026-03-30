'use client';
import React,{useState} from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';

export default function Login(){
  const r=useRouter();
  const [username,setU]=useState('admin');
  const [password,setP]=useState('admin123');
  const [err,setE]=useState<string|null>(null);
  async function submit(e:React.FormEvent){
    e.preventDefault(); setE(null);
    const res=await apiFetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
    if(!res.ok){ setE(`login failed ${res.status}`); return; }
    r.push('/notes');
  }
  return <div className="card" style={{maxWidth:480}}>
    <h1>Login</h1>
    <form onSubmit={submit}>
      <div><input style={{width:'100%'}} value={username} onChange={e=>setU(e.target.value)} placeholder="admin" /></div>
      <div style={{marginTop:8}}><input style={{width:'100%'}} type="password" value={password} onChange={e=>setP(e.target.value)} placeholder="admin123" /></div>
      <button style={{marginTop:8}} type="submit">Login</button>
    </form>
    {err? <p>❌ {err}</p>:null}
  </div>;
}
