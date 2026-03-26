import { cookies } from 'next/headers';

async function getSignedUrl(id: string): Promise<string> {
  const base = process.env.SERVER_API_BASE_URL || '';
  const cookieHeader = cookies().toString();
  // try mint a short-lived token url (works when logged in)
  try {
    const res = await fetch(`${base}/api/files/${encodeURIComponent(id)}/token`, {
      method: 'POST',
      headers: {
        cookie: cookieHeader,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: '',
      cache: 'no-store',
    });
    if (res.ok) {
      const j = (await res.json()) as any;
      if (j.download_url_with_token) return j.download_url_with_token;
      if (j.download_url) return j.download_url;
    }
  } catch {
    // ignore
  }
  return `/api/files/${encodeURIComponent(id)}/download`;
}

export default async function PdfViewerPage({ params }: { params: { id: string } }) {
  const id = params.id;
  const fileUrl = await getSignedUrl(id);
  const viewerSrc = `/pdfjs/web/viewer.html?file=${encodeURIComponent(fileUrl)}`;

  return (
    <div style={{ height: '100vh', width: '100vw' }}>
      <iframe title="PDF.js Viewer" src={viewerSrc} style={{ border: 'none', width: '100%', height: '100%' }} />
    </div>
  );
}
