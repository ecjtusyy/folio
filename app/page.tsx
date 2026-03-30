import Link from 'next/link';
export default function Page(){
  return <div className="card">
    <h1>Monorepo Demo</h1>
    <ul>
      <li><Link href="/login">/login</Link></li>
      <li><Link href="/notes">/notes</Link></li>
      <li><Link href="/posts">/posts</Link></li>
      <li><Link href="/admin/posts">/admin/posts</Link></li>
      <li><Link href="/imports">/imports</Link></li>
    </ul>
    <p>Health: <a href="/api/health">/api/health</a></p>
  </div>;
}
