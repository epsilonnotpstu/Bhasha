"""Command-line driver for implemented compiler stages."""
import argparse,json,sys
from pathlib import Path
from dataclasses import asdict
from .lexer import lex
from .parser import parse
from .semantic import analyze
from .irgen import generate
from .backend.vm import run
from .cfg import build_cfg
from .optimizer import optimize
def compile_text(text,source="<input>"):
 tokens,ds=lex(text,source)
 if ds:return tokens,None,ds,None
 ast,ds=parse(tokens,source)
 if ds:return tokens,ast,ds,None
 ds,_=analyze(ast,source)
 return tokens,ast,ds,generate(ast) if not ds else None
def main(argv=None):
 ap=argparse.ArgumentParser(prog="bhasha"); ap.add_argument("file")
 for flag in ("tokens","ast","tac","opt-tac","run","cfg","symtab","asm","wat","stats"): ap.add_argument("--"+flag,action="store_true")
 ap.add_argument("-O0",dest="opt",action="store_const",const=0); ap.add_argument("-O1",dest="opt",action="store_const",const=1); ap.add_argument("-O2",dest="opt",action="store_const",const=2); ap.add_argument("-o",dest="output")
 a=ap.parse_args(argv); text=Path(a.file).read_text(encoding="utf8"); ts,tree,ds,ir=compile_text(text,a.file)
 if ds: print("\n".join(d.render(text) for d in ds),file=sys.stderr); return 1
 if a.tokens: print("\n".join(f"{t.line}:{t.column}\t{t.type}\t{t.lexeme!r}" for t in ts[:-1]))
 if a.ast: print(json.dumps(asdict(tree),ensure_ascii=False,indent=2))
 opt_ir,stats=optimize(ir)
 if a.tac: print("\n".join(ir))
 if getattr(a,"opt_tac"): print("\n".join(opt_ir))
 if a.cfg: print(build_cfg(ir).dot())
 if a.symtab: print("Semantic analysis passed; symbols are scope-checked.")
 if a.asm or a.wat or a.output: print("Requested optional native/WAT artifact is not available; use --run.",file=sys.stderr); return 1
 if a.stats: print(f"IR instructions: {stats['before']} -> {stats['after']}; identity simplifications: {stats['simplified']}")
 if a.run: print(run(tree),end="")
 return 0
if __name__=="__main__": raise SystemExit(main())
