import { readFileSync, readdirSync } from 'fs';
import path from 'path';
import { markdownToHtml } from './markdown';
export type PostMeta={title:string;date:string;slug:string;summary:string;tags:string[]};
export type Post=PostMeta & {content:string;html:string};
const POSTS_DIR=path.join(process.cwd(),'content','posts');
function parseFrontmatter(raw:string):{meta:Record<string,string>;body:string}{if(!raw.startsWith('---\n'))throw new Error('Frontmatter must start with ---');const end=raw.indexOf('\n---\n',4);if(end===-1)throw new Error('Frontmatter closing --- not found');const frontmatter=raw.slice(4,end).split('\n');const meta:Record<string,string>={};for(const line of frontmatter){const idx=line.indexOf(':');if(idx===-1)continue;meta[line.slice(0,idx).trim()]=line.slice(idx+1).trim()}return {meta,body:raw.slice(end+5).trim()}}
function parseTags(value:string|undefined):string[]{if(!value)return [];return value.split(',').map((tag:string)=>tag.trim()).filter(Boolean)}
function ensureMeta(meta:Record<string,string>,fallbackSlug:string):PostMeta{const title=meta.title?.trim();const date=meta.date?.trim();const slug=(meta.slug?.trim()||fallbackSlug);const summary=meta.summary?.trim();if(!title||!date||!slug||!summary)throw new Error(`Missing required frontmatter in ${fallbackSlug}.md`);return {title,date,slug,summary,tags:parseTags(meta.tags)}}
export function getAllPostSlugs():string[]{return readdirSync(POSTS_DIR).filter((file:string)=>file.endsWith('.md')).map((file:string)=>file.replace(/\.md$/,''))}
export function getPostBySlug(slug:string):Post{const raw=readFileSync(path.join(POSTS_DIR,`${slug}.md`),'utf8');const {meta,body}=parseFrontmatter(raw);const normalized=ensureMeta(meta,slug);return {...normalized,content:body,html:markdownToHtml(body)}}
export function getAllPostsMeta():PostMeta[]{return getAllPostSlugs().map((slug)=>getPostBySlug(slug)).sort((a,b)=>(a.date<b.date?1:-1)).map(({title,date,slug,summary,tags})=>({title,date,slug,summary,tags}))}
