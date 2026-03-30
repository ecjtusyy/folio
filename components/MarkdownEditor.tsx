'use client';
import React, { useCallback, useMemo, useRef } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { markdown } from '@codemirror/lang-markdown';
import { keymap, EditorView } from '@codemirror/view';
import { indentWithTab } from '@codemirror/commands';

export function MarkdownEditor({value,onChange,onUploadImage}:{value:string;onChange:(v:string)=>void;onUploadImage:(f:File)=>Promise<string>}) {
  const viewRef = useRef<EditorView|null>(null);
  const exts = useMemo(()=>[markdown(), keymap.of([indentWithTab])],[]);
  const insert = useCallback((txt:string)=>{
    const view=viewRef.current; if(!view) return;
    const sel=view.state.selection.main;
    view.dispatch({changes:{from:sel.from,to:sel.to,insert:txt}});
    view.focus();
  },[]);
  const insertImage = useCallback(async (f:File)=>{
    const url = await onUploadImage(f);
    insert(`\n![](${url})\n`);
  },[onUploadImage, insert]);

  const onCreateEditor = useCallback((view:EditorView)=>{
    viewRef.current=view;
    const dom=view.dom;
    const onPaste = async (e:ClipboardEvent)=>{
      const cd=e.clipboardData; if(!cd) return;
      for (const item of Array.from(cd.items)) {
        if (item.type.startsWith('image/')) {
          const f=item.getAsFile(); if(f){ e.preventDefault(); await insertImage(f); }
          return;
        }
      }
    };
    const onDrop = async (e:DragEvent)=>{
      const dt=e.dataTransfer; if(!dt) return;
      const imgs=Array.from(dt.files||[]).filter(f=>f.type.startsWith('image/'));
      if(imgs.length){ e.preventDefault(); await insertImage(imgs[0]); }
    };
    const onDragOver=(e:DragEvent)=>e.preventDefault();
    dom.addEventListener('paste', onPaste);
    dom.addEventListener('drop', onDrop);
    dom.addEventListener('dragover', onDragOver);
  },[insertImage]);

  return <div className="card">
    <CodeMirror value={value} height="520px" extensions={exts} onChange={onChange} onCreateEditor={onCreateEditor} />
  </div>;
}
