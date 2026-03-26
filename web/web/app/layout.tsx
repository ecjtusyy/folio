import './globals.css';
import 'katex/dist/katex.min.css';
import Link from 'next/link';
import React from 'react';

export default function RootLayout({children}:{children:React.ReactNode}) {
  return (
    <html lang="zh">
      <body>
        <nav className="nav">
          <Link href="/">Home</Link>
          <Link href="/login">Login</Link>
          <Link href="/notes">Notes</Link>
          <Link href="/posts">Blog</Link>
          <Link href="/admin/posts">Admin Posts</Link>
          <Link href="/imports">Imports</Link>
        </nav>
        <div className="container">{children}</div>
      </body>
    </html>
  );
}
