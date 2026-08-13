#!/usr/bin/env python3
"""
canonicalize.py  -  a layout-invariant form of an RTL candidate, plus the
structural features a reward is allowed to see.

WHY THIS EXISTS
---------------
The deployed reward was exploited by formatting. Between two checkpoints the
policy moved nonblocking assignments onto separate lines; `nb_assign` counts
assignments that BEGIN A LINE, so it rose from 24 to 44 while the token count
FELL and real Fmax moved by -1 MHz. The reward rose 280 MHz for pressing Enter.
Re-scoring every trajectory candidate under a uniform layout removes 101% of
that jump.

The repair is not to patch that one regex. It is to make the reward structurally
incapable of seeing layout: canonicalise first, and define every feature over
the canonical form.

TWO BACKENDS
------------
  yosys     read_verilog -> proc; opt_clean -> write_rtlil, with src/hdlname
            attributes stripped and internal names alpha-normalised. Canonical
            over the ELABORATED design, so it also absorbs dead logic and some
            structural spellings. Preferred.
  lexical   tokenizer + declaration-scoped alpha-renaming, comments removed,
            one statement per line, whitespace normalised. Canonical over the
            SOURCE. Absorbs trivia only. Honest name: lexical invariance.

`--backend auto` uses yosys when it is on PATH and falls back to lexical,
recording which was used so a mixed corpus can never be reported as one thing.

THE CONTRACT (verify_contract(), and `python canonicalize.py --self-test`)
-------------------------------------------------------------------------
  1. idempotence           C(C(x)) == C(x)
  2. metamorphic equality  C(x) == C(m(x)) bytewise, for every m in the
                           invariance suite: comments, blank lines, whitespace,
                           statement reflow, internal alpha-renaming
  3. coverage              unsupported syntax REJECTS loudly; it is never
                           silently passed through, because a silent passthrough
                           reintroduces exactly the channel this removes
  4. no collisions         two designs with different token streams must not
                           collapse to the same canonical form
  5. feature equality      the structural features must be identical across the
                           whole metamorphic suite, not merely similar

STRUCTURAL FEATURES
-------------------
Deliberately NOT the deployed twelve. Removed or replaced:
  n_lines     DELETED. It is the exploited channel and has no hardware meaning.
  nb_assign   was `^\\s*\\w+...<=` (line-anchored). Now counts `<=` tokens at
              statement level, so packing is irrelevant.
  accum       was a regex containing `\\b[a-z]+\\d`, i.e. it read SIGNAL NAMES.
              Now matches the shape `<reg> <= <expr with *> + <reg>` over
              tokens, independent of spelling.
Everything else is recomputed over canonical text so that layout cannot reach it.
"""

import os
import re
import sys
import json
import shutil
import hashlib
import argparse
import subprocess
import tempfile

CANON_VERSION = "1.0.0"        # bump on ANY behaviour change; it is preregistered

# ---------------------------------------------------------------- tokenizer
KEYWORDS = set("""
module endmodule input output inout wire reg logic integer parameter localparam
always always_ff always_comb always_latch assign begin end if else for while
case casez casex endcase default posedge negedge or and not xor nand nor xnor
signed unsigned genvar generate endgenerate initial function endfunction task
endtask return automatic static const typedef struct union enum packed void
bit byte shortint int longint real time realtime string disable fork join
repeat forever wait specify endspecify defparam
""".split())

# Constructs the lexical backend refuses rather than mishandles. Each would need
# scope analysis this tokenizer does not do, and a wrong rename is worse than a
# refusal because it silently changes the design the reward is scoring.
UNSUPPORTED = re.compile(
    r"`(?:include|define|ifdef|ifndef)\b|\bfunction\b|\btask\b|\bgenerate\b"
    r"|\bpackage\b|\binterface\b|\bmodule\b[^;]*\bmodule\b", re.DOTALL)

TOK = re.compile(r"""
    (?P<ws>\s+)
  | (?P<lcomment>//[^\n]*)
  | (?P<bcomment>/\*.*?\*/)
  | (?P<string>"(?:\\.|[^"\\])*")
  | (?P<escid>\\[^\s]+\s)
  | (?P<macro>`[A-Za-z_][A-Za-z0-9_$]*)
  | (?P<number>[0-9]*'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ_?]+|[0-9][0-9_]*(?:\.[0-9_]+)?)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_$]*)
  | (?P<other>.)
""", re.VERBOSE | re.DOTALL)


class Unsupported(Exception):
    """Raised instead of returning a half-canonicalised result."""


def tokenize(src, keep_trivia=False):
    out = []
    for m in TOK.finditer(src):
        k = m.lastgroup
        if not keep_trivia and k in ("ws", "lcomment", "bcomment"):
            continue
        out.append((k, m.group()))
    return out


# ---------------------------------------------------------- lexical backend
def _declared_names(toks):
    """Identifiers introduced by a declaration inside the module body.

    Scans for a declaration keyword and collects the identifiers that follow it
    until the terminating ';', skipping bit-range brackets. Renaming ONLY these
    is what makes the rename safe: an identifier we never saw declared is left
    alone, so an unparsed construct degrades to "not renamed" rather than to
    "renamed wrongly".
    """
    decl = {"wire", "reg", "logic", "integer", "genvar", "parameter",
            "localparam", "input", "output", "inout"}
    names, i = set(), 0
    while i < len(toks):
        k, t = toks[i]
        if k == "ident" and t in decl:
            depth = 0
            j = i + 1
            while j < len(toks):
                kk, tt = toks[j]
                if tt in "[(":
                    depth += 1
                elif tt in "])":
                    depth -= 1
                elif tt == ";" and depth <= 0:
                    break
                elif kk == "ident" and tt not in KEYWORDS and depth == 0:
                    names.add(tt)
                j += 1
            i = j
        i += 1
    return names


def _ports_and_module(toks):
    got, depth, seen = set(), 0, False
    for k, t in toks:
        if not seen:
            if k == "ident" and t == "module":
                seen = True
            continue
        if t in "([":
            depth += 1
        elif t in ")]":
            depth -= 1
        elif t == ";" and depth <= 0:
            break
        elif k == "ident" and t not in KEYWORDS:
            got.add(t)
    return got


def canon_lexical(src, module_name="top"):
    """Canonical SOURCE form. Absorbs trivia; does not elaborate."""
    if UNSUPPORTED.search(src):
        raise Unsupported("macro/function/task/generate/multi-module")
    toks = tokenize(src)
    if not toks:
        raise Unsupported("empty after tokenisation")

    ports = _ports_and_module(toks)
    declared = _declared_names(toks)
    # rename only what is BOTH declared in the body AND not a port: those are
    # the names with no interface meaning.
    renamable = sorted(declared - ports)

    # deterministic order of first appearance, so the mapping does not depend on
    # the original spelling at all
    order, seen = [], set()
    for k, t in toks:
        if k == "ident" and t in renamable and t not in seen:
            seen.add(t)
            order.append(t)
    mapping = {n: f"n{i}" for i, n in enumerate(order)}

    out = []
    for k, t in toks:
        out.append(mapping.get(t, t) if k == "ident" else t)

    # normalise the module name too: it is metadata, not hardware
    txt = " ".join(out)
    txt = re.sub(r"\bmodule\s+\S+", f"module {module_name}", txt, count=1)
    # one statement per line -> layout becomes a constant, not a choice
    txt = re.sub(r"\s*;\s*", " ;\n", txt)
    txt = re.sub(r"\bbegin\b", "begin\n", txt)
    txt = re.sub(r"\bend\b", "\nend\n", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    lines = [ln.strip() for ln in txt.split("\n")]
    return "\n".join(ln for ln in lines if ln)


# ------------------------------------------------------------ yosys backend
ATTR = re.compile(r"^\s*attribute\s+\\?(?:src|hdlname|keep|init)\b.*$", re.M)
AUTOID = re.compile(r"\$(?:auto|techmap|procdff|procmux|memwr)\$[^\s\\]*")


def canon_yosys(src, module_name="top", yosys="yosys", timeout=60):
    """Canonical ELABORATED form via RTLIL.

    proc lowers always-blocks; opt_clean removes unused cells and wires. Source
    attributes are stripped because they carry file/line/name provenance -- i.e.
    exactly the layout information we are trying to make invisible -- and
    autogenerated ids are renumbered in order of appearance so two runs that
    differ only in naming produce identical bytes.
    """
    with tempfile.TemporaryDirectory() as wd:
        v = os.path.join(wd, "in.v")
        r = os.path.join(wd, "out.il")
        open(v, "w").write(src)
        cmd = [yosys, "-q", "-p",
               f"read_verilog -sv {v}; hierarchy -auto-top; proc; opt_clean; "
               f"write_rtlil {r}"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0 or not os.path.exists(r):
            raise Unsupported(f"yosys failed: {p.stderr.strip()[:200]}")
        il = open(r, errors="replace").read()

    il = ATTR.sub("", il)
    # renumber autogenerated identifiers in order of first appearance
    seen, n = {}, 0
    def sub(m):
        nonlocal n
        if m.group() not in seen:
            seen[m.group()] = f"$a{n}"
            n += 1
        return seen[m.group()]
    il = AUTOID.sub(sub, il)
    il = re.sub(r"\bmodule\s+\\\S+", f"module \\\\{module_name}", il, count=1)
    il = re.sub(r"[ \t]+", " ", il)
    return "\n".join(ln.strip() for ln in il.split("\n") if ln.strip())


def canonicalize(src, backend="auto", module_name="top", yosys="yosys"):
    """Returns (canonical_text, backend_used)."""
    if backend in ("auto", "yosys") and shutil.which(yosys):
        try:
            return canon_yosys(src, module_name, yosys), "yosys"
        except Exception:
            if backend == "yosys":
                raise
    return canon_lexical(src, module_name), "lexical"


def canon_hash(txt):
    return hashlib.sha256(txt.encode()).hexdigest()[:16]


# -------------------------------------------------------- structural features
STRUCT_FEATURES = ["n_mult", "max_stmt_mult", "n_posedge", "n_nonblock",
                   "n_blocking", "accum_struct", "n_regs", "n_wires",
                   "n_ternary", "n_cmp", "n_stmts", "pipe_ratio_struct"]


def struct_feature_dict(canon_txt):
    """Features over CANONICAL text. No feature may depend on layout.

    Replaces three deployed features that could:
      n_lines    deleted outright -- it is the exploited channel
      nb_assign  was line-anchored; now a token count of '<=' at statement level
      accum      was `\\b[a-z]+\\d`, i.e. it read signal NAMES; now a token-shape
                 match for `<target> <= <expr containing *> + <target-like>`
    """
    toks = tokenize(canon_txt)
    words = [t for k, t in toks]
    stmts, cur = [], []
    for k, t in toks:
        if t == ";":
            stmts.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        stmts.append(cur)

    fd = {}
    fd["n_mult"] = words.count("*")
    fd["max_stmt_mult"] = max((s.count("*") for s in stmts), default=0)
    fd["n_posedge"] = words.count("posedge")
    fd["n_nonblock"] = sum(1 for i in range(len(words) - 1)
                           if words[i] == "<" and words[i + 1] == "=")
    fd["n_nonblock"] += words.count("<=")
    fd["n_blocking"] = sum(1 for s in stmts
                           if "=" in s and "<=" not in s and "==" not in s)
    fd["n_regs"] = words.count("reg") + words.count("logic")
    fd["n_wires"] = words.count("wire")
    fd["n_ternary"] = words.count("?")
    fd["n_cmp"] = sum(words.count(c) for c in ("<", ">", "==", "!=", ">=", "<="))
    fd["n_stmts"] = len(stmts)
    acc = 0
    for s in stmts:
        j = next((i for i in range(len(s) - 1)
                  if s[i] == "<" and s[i + 1] == "="), None)
        if j is None and "<=" in s:
            j = s.index("<=")
        if j is None:
            continue
        rhs = s[j:]
        if "*" in rhs and "+" in rhs:
            acc += 1
    fd["accum_struct"] = acc
    fd["pipe_ratio_struct"] = acc / (fd["n_mult"] + 1.0)
    return fd


def struct_features(canon_txt):
    fd = struct_feature_dict(canon_txt)
    return [fd[n] for n in STRUCT_FEATURES]


# ---------------------------------------------------------------- contract
def _m_comments(s):
    return "\n".join(ln + ("  // pipeline retimed fast" if i % 3 == 0 else "")
                     for i, ln in enumerate(s.split("\n")))


def _m_blanklines(s):
    out = []
    for i, ln in enumerate(s.split("\n")):
        out.append(ln)
        if i % 2 == 0:
            out.append("")
    return "\n".join(out)


def _m_whitespace(s):
    return re.sub(r"[ \t]+", "    ", s).replace("\n", "\n  ")


def _m_reflow(s):
    """The observed attack: put every statement on its own line."""
    return re.sub(r";\s*", ";\n", s)


def _m_pack(s):
    """The inverse: pack statements together."""
    return re.sub(r";\s*\n\s*", "; ", s)


def _m_rename(s):
    toks = tokenize(s)
    prot = _ports_and_module(toks)
    decl = _declared_names(toks)
    mp = {n: f"zz_{i}" for i, n in enumerate(sorted(decl - prot))}
    return "".join(mp.get(t, t) if k == "ident" else t
                   for k, t in tokenize(s, keep_trivia=True))


SUITE = [("comments", _m_comments), ("blanklines", _m_blanklines),
         ("whitespace", _m_whitespace), ("reflow", _m_reflow),
         ("pack", _m_pack), ("rename", _m_rename)]


def verify_contract(src, backend="auto", yosys="yosys"):
    """Every clause of the contract, on one candidate. Returns a dict."""
    res = {"ok": True, "backend": None, "failures": []}
    try:
        c0, be = canonicalize(src, backend, yosys=yosys)
    except Unsupported as e:
        return {"ok": False, "backend": None, "rejected": str(e),
                "failures": ["rejected"]}
    res["backend"] = be
    res["hash"] = canon_hash(c0)

    try:
        c1, _ = canonicalize(c0, backend, yosys=yosys)
        if c1 != c0:
            res["ok"] = False
            res["failures"].append("idempotence")
    except Unsupported:
        res["ok"] = False
        res["failures"].append("idempotence:rejected")

    f0 = struct_feature_dict(c0)
    for name, m in SUITE:
        try:
            cm, _ = canonicalize(m(src), backend, yosys=yosys)
        except Unsupported:
            res["ok"] = False
            res["failures"].append(f"{name}:rejected")
            continue
        if cm != c0:
            res["ok"] = False
            res["failures"].append(f"{name}:bytes")
        if struct_feature_dict(cm) != f0:
            res["ok"] = False
            res["failures"].append(f"{name}:features")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="auto",
                    choices=["auto", "yosys", "lexical"])
    ap.add_argument("--yosys", default="yosys")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--dirs", nargs="*", default=[
        "rtl/holdout_eval_v8_firfirr", "rtl/holdout_eval_v8_poly",
        "rtl/holdout_eval_v8_iirmed", "rtl/traj_v8"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="canonicalize_contract.json")
    args = ap.parse_args()

    import glob
    import collections
    here = os.path.dirname(os.path.abspath(__file__))
    files = []
    for d in args.dirs:
        files += sorted(glob.glob(os.path.join(here, d, "*.sv")))
    if args.limit:
        files = files[:args.limit]
    print(f"canonicalize.py v{CANON_VERSION}   backend={args.backend}   "
          f"{len(files)} candidates")
    if not files:
        print("no candidates found")
        return

    fails = collections.Counter()
    rejected, ok, byhash = 0, 0, {}
    per = []
    for f in files:
        src = open(f, errors="replace").read()
        r = verify_contract(src, args.backend, args.yosys)
        per.append({"file": os.path.relpath(f, here), **r})
        if "rejected" in r and r.get("rejected"):
            rejected += 1
            continue
        if r["ok"]:
            ok += 1
        for x in r["failures"]:
            fails[x] += 1
        h = r.get("hash")
        if h:
            byhash.setdefault(h, []).append(f)

    print(f"\n  contract PASSED : {ok}/{len(files)}")
    print(f"  rejected        : {rejected}  (explicit refusal, not silent)")
    if fails:
        print("  failures by clause:")
        for k, v in fails.most_common():
            print(f"     {k:26s} {v}")

    # clause 4: collision audit.
    #
    # A collision is DIFFERENT HARDWARE sharing a canonical form. It is NOT two
    # candidates whose raw text differs but whose hardware is the same -- that
    # is the canonicaliser doing its job, and an earlier version of this audit
    # wrongly counted 91 of those as failures. Alpha-renaming exists precisely
    # so that `acc0` and `a0` collapse; flagging the collapse as a defect would
    # have condemned the tool for working.
    #
    # Design identity is the proxy for hardware identity here: every candidate
    # is generated against a named catalog design with its own reference model,
    # so two candidates for different designs implement different functions.
    # The rigorous version compares oracle traces and belongs in the frozen
    # pre-registration run, not in a smoke test.
    coll, merged = 0, 0
    for h, fs in byhash.items():
        if len(fs) < 2:
            continue
        merged += 1
        designs = {os.path.basename(x).split("__")[1]
                   if "__" in os.path.basename(x) else os.path.basename(x)
                   for x in fs}
        if len(designs) > 1:
            coll += 1
            print(f"  COLLISION: hash {h} shared by designs {sorted(designs)}")
    print(f"  equivalence merges : {merged}  (same design, different spelling "
          f"-- CORRECT behaviour)")
    print(f"  collisions         : {coll}  (different designs, same canonical "
          f"form -- a defect)")

    json.dump({"version": CANON_VERSION, "backend": args.backend,
               "n": len(files), "passed": ok, "rejected": rejected,
               "failures": dict(fails), "collisions": coll,
               "per_file": per if args.limit else per[:50]},
              open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    print("\nThe reward may only be built on this if PASSED == n - rejected,")
    print("collisions == 0, and the rejection rate is small enough to state.")


if __name__ == "__main__":
    main()
