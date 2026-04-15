export default function MarkdownRenderer({ html }: { html: string }) { return <div className="markdown" dangerouslySetInnerHTML={{ __html: html }} />; }
