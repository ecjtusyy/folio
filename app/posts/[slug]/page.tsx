import { notFound } from 'next/navigation';
import MarkdownRenderer from '@/components/MarkdownRenderer';
import { getAllPostSlugs, getPostBySlug } from '@/lib/posts';
export function generateStaticParams(){return getAllPostSlugs().map((slug)=>({slug}))}
export default function PostDetailPage({params}:{params:{slug:string}}){try{const post=getPostBySlug(params.slug);return <article className="post-shell"><p className="eyebrow">Post</p><h1 className="page-title">{post.title}</h1><div className="post-meta">{post.date}</div><p className="post-summary">{post.summary}</p><MarkdownRenderer html={post.html} /></article>}catch{notFound()}}
