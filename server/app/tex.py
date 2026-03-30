from __future__ import annotations
import os, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from .config import settings

class TexCompileError(Exception):
    def __init__(self, message: str, tail: str = "", candidates: list[str] | None = None):
        super().__init__(message)
        self.tail = tail
        self.candidates = candidates or []

def _tail(text: str, n: int) -> str:
    arr = text.splitlines()
    return "\n".join(arr[-n:])

def _safe_relpath(p: str) -> str:
    # zip paths are posix-like
    p = p.replace("\\", "/").strip()
    # disallow absolute or traversal
    if p.startswith("/") or p.startswith("..") or "/.." in p:
        raise TexCompileError("invalid_main_tex_path")
    return p

def _detect_main_tex(job_dir: Path, requested: str | None) -> Path:
    # 1) backward compatibility: root main.tex
    main_root = job_dir / "main.tex"
    if main_root.exists():
        return main_root

    # 2) user requested
    if requested:
        rel = _safe_relpath(requested)
        cand = job_dir / rel
        if cand.exists() and cand.is_file() and cand.suffix.lower() == ".tex":
            return cand
        raise TexCompileError("requested_main_tex_not_found", candidates=[])

    # 3) auto detect
    tex_files = [p for p in job_dir.rglob("*.tex") if p.is_file()]
    if len(tex_files) == 0:
        raise TexCompileError("no_tex_files_found")

    if len(tex_files) == 1:
        return tex_files[0]

    def looks_like_main(p: Path) -> bool:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return False
        return ("\documentclass" in t) and ("\begin{document}" in t)

    mains = [p for p in tex_files if looks_like_main(p)]
    if len(mains) == 1:
        return mains[0]

    candidates = sorted([str(p.relative_to(job_dir)).replace("\\", "/") for p in (mains or tex_files)])
    raise TexCompileError("main_tex_ambiguous", tail="", candidates=candidates)

def compile_tex_zip(zip_bytes: bytes, main_tex: str | None = None) -> bytes:
    root = os.path.join(settings.app_tmp_dir, "texjobs")
    os.makedirs(root, exist_ok=True)
    job = tempfile.mkdtemp(prefix="job_", dir=root)
    try:
        zp = os.path.join(job, "src.zip")
        with open(zp, "wb") as f:
            f.write(zip_bytes)

        with zipfile.ZipFile(zp, "r") as zf:
            zf.extractall(job)

        job_dir = Path(job)
        main_path = _detect_main_tex(job_dir, main_tex)
        rel_main = str(main_path.relative_to(job_dir)).replace("\\", "/")

        proc = subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", rel_main],
            cwd=job,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=settings.tex_compile_timeout_seconds
        )
        out = proc.stdout or ""
        if proc.returncode != 0:
            raise TexCompileError("latexmk_failed", tail=_tail(out, settings.tex_log_tail_lines))

        pdf_path = main_path.with_suffix(".pdf")
        if not pdf_path.exists():
            # latexmk may output to cwd with base name
            pdf_path = job_dir / (main_path.stem + ".pdf")
        if not pdf_path.exists():
            raise TexCompileError("pdf_not_found_after_compile", tail=_tail(out, settings.tex_log_tail_lines))

        return pdf_path.read_bytes()
    except subprocess.TimeoutExpired as e:
        raise TexCompileError("latexmk_timeout", tail=_tail((e.stdout or "") + "\n" + (e.stderr or ""), settings.tex_log_tail_lines))
    finally:
        try:
            shutil.rmtree(job)
        except Exception:
            pass
