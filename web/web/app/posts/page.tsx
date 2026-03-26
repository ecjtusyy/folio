import Link from 'next/link';
export const dynamic='force-dynamic';
async function getPosts(){
  const base=process.env.SERVER_API_BASE_URL||'http://server:8000';
  const res=await fetch(`${base}/api/public/posts`,{cache:'no-store'});
  if(!res.ok) return [];
  return await res.json();
}
export default async function Posts(){
  const posts=await getPosts();
  return <div>
    <h1>Blog</h1>
    <div className="card">
      <ul>{posts.map((p:any)=><li key={p.slug}><Link href={`/posts/${p.slug}`}><b>{p.title}</b></Link><div>{p.summary||''}</div></li>)}</ul>
    </div>
  </div>;
}
