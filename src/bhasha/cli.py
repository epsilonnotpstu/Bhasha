"""Command-line driver for implemented compiler stages."""
import argparse,json,sys,subprocess
from pathlib import Path
from dataclasses import asdict
from .lexer import lex
from .parser import parse
from .semantic import analyze
from .irgen import generate
from .backend.vm import run
from .cfg_new import build_cfg
from .optimizer import optimize
from .backend.native_x86 import emit_native
from .backend.wasm import emit_wat, WasmError
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
 if a.output:
  try:
   c=emit_native(tree,a.output); print(f"native ELF: {a.output} (generated C: {c})")
  except (OSError,subprocess.CalledProcessError,ValueError) as e: print(f"native backend error: {e}",file=sys.stderr);return 1
 if a.wat:
  try: print(emit_wat(tree),end="")
  except WasmError as e: print(f"WAT backend error: {e}",file=sys.stderr); return 1
 if a.asm: print("Direct assembly text is not implemented; native compilation uses generated C.",file=sys.stderr)
 if a.stats: print(f"IR instructions: {stats['before']} -> {stats['after']}; folds: {stats['constant_folds']}; simplified: {stats['simplified']}; dead: {stats['dead_code']}")
 if a.run: print(run(tree),end="")
 return 0
if __name__=="__main__": raise SystemExit(main())
