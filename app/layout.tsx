import './globals.css';
import type { Metadata } from 'next';
import SiteHeader from '@/components/SiteHeader';
export const metadata: Metadata = { title: 'SYY | Personal Site', description: 'Personal profile, articles, papers, and projects.' };
export default function RootLayout({ children }: { children: React.ReactNode }) { return <html lang="en"><body><div className="site-shell"><SiteHeader /><main className="site-main"><div className="container">{children}</div></main><footer className="site-footer"><div className="container footer-inner"><p>© 2026 SYY. Static site for GitHub Pages.</p></div></footer></div></body></html>; }
