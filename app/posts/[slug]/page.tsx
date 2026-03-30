import { notFound } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
export const dynamic='force-dynamic';

async function getPost(slug:string){
  const base=process.env.SERVER_API_BASE_URL||'http://server:8000';
  const res=await fetch(`${base}/api/public/posts/${encodeURIComponent(slug)}`,{cache:'no-store'});
  if(!res.ok) return null;
  return await res.json();
}
export default async function Post({params}:{params:{slug:string}}){
  const p=await getPost(params.slug);
  if(!p) return notFound();
  return <div>
    <h1>{p.title}</h1>
    <div className="card">
      <ReactMarkdown remarkPlugins={[remarkGfm,remarkMath]} rehypePlugins={[rehypeKatex]}>{p.content_md}</ReactMarkdown>
    </div>
  </div>;
}
