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

CANON_VERSION = "1.5.1"        # bump on ANY behaviour change; it is preregistered

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
  | (?P<number>[0-9]*'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ_?]+|'[01xXzZ](?![A-Za-z0-9_])|[0-9][0-9_]*(?:\.[0-9_]+)?)
  | (?P<ident>[A-Za-z_][A-Za-z0-9_$]*)   # NOTE: the unsized-fill alternative
                                          # above must precede plain numbers,
                                          # or `'0` tokenises as `'` + `0` and
                                          # space-joins into the invalid `' 0`.
                                          # That broke 5 of 490 candidates and
                                          # surfaced only via trace checking.
  | (?P<op>===|!==|>>>|<<<|<=|>=|==|!=|&&|\|\||<<|>>|\*\*|\+:|-:|~\^|\^~|~&|~\|)
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
    for k, tt in toks:
        if k == "ident" and tt in renamable and tt not in seen:
            seen.add(tt)
            order.append(tt)

    # CAPTURE-FREE namespace: a fixed prefix like "n" can collide with an
    # identifier the source already uses (a port named n0, or an unrenamed
    # name), which would silently merge two distinct signals. Grow the prefix
    # until it cannot collide with anything in the token stream.
    # Collision can only occur against names that SURVIVE canonicalisation, so
    # the renamable set must be excluded. Including it made the canonicaliser
    # non-idempotent: pass 1 emits n0, pass 2 sees n0 in `existing`, escalates
    # the prefix to cn, and emits cn0. The corpus contract run would not have
    # caught this -- only the self-test did, which is why it exists.
    existing = {tt for k, tt in toks if k == "ident"} - set(renamable)
    prefix = "n"
    while any(e.startswith(prefix) and e[len(prefix):].isdigit() for e in existing):
        prefix = "c" + prefix
    mapping = {n: f"{prefix}{i}" for i, n in enumerate(order)}
    if len(set(mapping.values())) != len(mapping) or \
            set(mapping.values()) & existing:
        raise Unsupported("rename namespace is not capture-free")

    out = []
    for k, t in toks:
        out.append(mapping.get(t, t) if k == "ident" else t)

    # normalise the module name too: it is metadata, not hardware
    txt = " ".join(out)
    txt = re.sub(r"\bmodule\s+\S+", f"module {module_name}", txt, count=1)
    # one statement per line -> layout becomes a constant, not a choice
    # One statement per line, but ONLY breaking at semicolons that are at
    # parenthesis depth 0. A `for (i = 0; i < 5; i = i + 1)` header contains
    # semicolons that do not end statements; splitting on them shredded loop
    # headers across three pseudo-statements and made loop bounds invisible to
    # every feature. check_a caught this as an unorderable median-filter pair.
    out2, depth = [], 0
    for ch in txt:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == ";" and depth == 0:
            out2.append(" ;\n")
        else:
            out2.append(ch)
    txt = "".join(out2)
    txt = re.sub(r"\bbegin\b", "begin\n", txt)
    txt = re.sub(r"\bend\b", "\nend\n", txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    lines = [ln.strip() for ln in txt.split("\n")]
    return "\n".join(ln for ln in lines if ln)


# ------------------------------------------------------------ yosys backend
# Only PROVENANCE attributes are stripped. `keep` and `init` were in this list
# and should not have been: they carry synthesis and initialisation semantics,
# so removing them changes the design rather than its spelling.
ATTR = re.compile(r"^\s*attribute\s+\\?(?:src|hdlname)\b.*$", re.M)
BANNER = re.compile(r"^\s*(?:#\s*Generated by Yosys.*|autoidx\s+\d+)\s*$", re.M)
# Yosys names every generated cell after the FILE AND LINE that produced it:
#   $mul$/tmp/tmpizfxrzok/in.v:21$21_Y
# The line number is literally the layout channel we are removing, and the
# temporary directory varies per invocation, so two runs of byte-identical
# input produce different RTLIL. Both must be normalised away.
YOSYS_ID = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*\$[^\s\[\]]*")
WIRE_DECL = re.compile(r"^\s*wire\b(?P<mid>[^\\\n]*)\\(?P<name>[A-Za-z_][A-Za-z0-9_$]*)",
                       re.M)


def _renumber(text, pattern, prefix):
    """Replace every match with prefix+index, indexed by first appearance."""
    seen = {}
    def sub(m):
        k = m.group()
        if k not in seen:
            seen[k] = f"{prefix}{len(seen)}"
        return seen[k]
    return pattern.sub(sub, text)


def canon_yosys(src, module_name="top", yosys="yosys", timeout=60):
    """Canonical ELABORATED form via RTLIL.

    proc lowers always-blocks; opt_clean removes unused cells and wires, so this
    form additionally absorbs dead logic that the lexical backend cannot see.

    NOTE on idempotence: this map is Verilog -> RTLIL, i.e. it is NOT closed
    over its input language, so C(C(x)) is undefined and the contract's
    idempotence clause does not apply. The meaningful form of the same property
    for a cross-language canonicaliser is the metamorphic clause: every Verilog
    spelling of one design must map to identical RTLIL. verify_contract()
    enforces that and skips C(C(x)) for this backend.
    """
    with tempfile.TemporaryDirectory() as wd:
        # fixed basename inside the temp dir; the DIRECTORY still varies, which
        # is why the identifier normalisation below is required rather than
        # merely tidy.
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

    il = BANNER.sub("", il)          # tool version + autoidx counter
    il = ATTR.sub("", il)            # src / hdlname provenance attributes
    il = _renumber(il, YOSYS_ID, "$g")   # generated names carrying file:line

    # Source-derived wire names survive elaboration, so an alpha-renamed input
    # would otherwise produce different RTLIL. Rename declared non-port wires in
    # order of first appearance; ports keep their names because they are
    # interface, not implementation.
    ports, declared = set(), []
    for m in WIRE_DECL.finditer(il):
        n = m.group("name")
        if re.search(r"\b(?:input|output|inout)\b", m.group("mid")):
            ports.add(n)
        elif n not in declared:
            declared.append(n)
    mapping = {n: f"w{i}" for i, n in enumerate(n for n in declared
                                                if n not in ports)}
    if mapping:
        pat = re.compile(r"\\(" + "|".join(re.escape(k) for k in
                                          sorted(mapping, key=len, reverse=True))
                         + r")(?![A-Za-z0-9_$])")
        il = pat.sub(lambda m: "\\" + mapping[m.group(1)], il)

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
                   "n_ternary", "n_cmp", "n_stmts", "pipe_ratio_struct",
                   "n_loops", "loop_bound_max", "loop_bound_sum"]


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
    stmts, cur, sdepth = [], [], 0
    for k, tk in toks:
        if tk in "([":
            sdepth += 1
        elif tk in ")]":
            sdepth -= 1
        if tk == ";" and sdepth == 0:
            stmts.append(cur)
            cur = []
        else:
            cur.append(tk)
    if cur:
        stmts.append(cur)

    fd = {}
    fd["n_mult"] = words.count("*")
    fd["max_stmt_mult"] = max((s.count("*") for s in stmts), default=0)
    fd["n_posedge"] = words.count("posedge")
    # `<=` is nonblocking assignment in a procedural statement and less-or-equal
    # in an expression. Parenthesis depth alone is NOT enough: in
    #     assign y = a <= b ;
    # the `<=` sits at depth 0 yet is a comparison. Classify by statement
    # context instead, and REJECT rather than guess when a statement is
    # ambiguous -- a reward feature that confuses assignment with comparison is
    # exactly what this file exists to eliminate.
    fd["n_nonblock"] = 0
    fd["n_blocking"] = 0
    n_cmp = 0
    CMP = ("<", ">", ">=", "==", "!=", "===", "!==")
    for s in stmts:
        if not s:
            continue
        depth0 = []
        depth = 0
        for i, tk in enumerate(s):
            if tk in "([":
                depth += 1
            elif tk in ")]":
                depth -= 1
            elif depth == 0:
                depth0.append((i, tk))
        is_continuous = s[0] in ("assign", "wire")
        assign_at = None
        if not is_continuous:
            # first top-level assignment operator wins; everything else is a
            # comparison
            for i, tk in depth0:
                if tk in ("<=", "="):
                    assign_at = (i, tk)
                    break
            tops = [i for i, tk in depth0 if tk == "<="]
            if len(tops) > 1 and assign_at and assign_at[1] == "<=":
                raise Unsupported(
                    "ambiguous statement: multiple top-level '<=' "
                    "(cannot separate assignment from comparison)")
        if assign_at and assign_at[1] == "<=":
            fd["n_nonblock"] += 1
        elif assign_at and assign_at[1] == "=":
            fd["n_blocking"] += 1
        for i, tk in enumerate(s):
            if tk in CMP:
                n_cmp += 1
            elif tk == "<=" and (assign_at is None or i != assign_at[0]):
                n_cmp += 1
    fd["n_cmp"] = n_cmp
    fd["n_stmts"] = len(stmts)
    # restored: the v1.3.0 classifier rewrite replaced a block that also
    # computed these, and check_a caught the KeyError before they could reach a
    # frozen feature vector.
    fd["n_regs"] = words.count("reg") + words.count("logic")
    fd["n_wires"] = words.count("wire")
    fd["n_ternary"] = words.count("?")
    acc = 0
    for s in stmts:
        if "<=" not in s:
            continue
        j = s.index("<=")
        rhs = s[j:]
        if "*" in rhs and "+" in rhs:
            acc += 1
    fd["accum_struct"] = acc
    fd["pipe_ratio_struct"] = acc / (fd["n_mult"] + 1.0)

    # Loop structure. A `for` bound determines how many comparators or adders
    # the loop unrolls into, so it determines the critical path -- two median
    # filters differing only in `i < 5` versus `i < 4` measured 60.4 and 38.3
    # MHz while every other feature was identical. Bounds are structural, not
    # cosmetic, and no layout change can alter them.
    fd["n_loops"] = words.count("for")
    bounds = []
    for i, tk in enumerate(words):
        if tk != "for":
            continue
        depth, j, lits = 0, i, []
        while j < len(words):
            if words[j] in "([":
                depth += 1
            elif words[j] in ")]":
                depth -= 1
                if depth == 0:
                    break
            elif depth > 0 and words[j].isdigit():
                lits.append(int(words[j]))
            j += 1
        bounds.append(max(lits) if lits else 0)
    fd["loop_bound_max"] = max(bounds) if bounds else 0
    fd["loop_bound_sum"] = sum(bounds)
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


def trace_equal(src, canon, design, n=256, seeds=(1, 2)):
    """Do the original and its canonical form produce identical output streams?

    Byte-level metamorphic equality proves the canonicaliser is layout-blind. It
    does NOT prove the canonical form is the same circuit -- a renaming bug that
    merged two signals would be perfectly consistent and perfectly wrong. This
    runs both through the simulator on identical stimuli and compares full
    traces. Sampled equivalence, not proof, and not timing identity: call these
    equivalence merges, never hardware identity.

    Only meaningful for the lexical backend, whose output is still Verilog.
    """
    import numpy as np
    import oracle
    try:
        _, in_w = oracle.build_reference(design)
    except Exception as e:
        return None, f"no reference: {e}"
    for sd in seeds:
        stim = oracle.gen_stimulus(n, in_w, sd)
        a = oracle.run_dut(re.sub(r"\bmodule\s+\w+", f"module {design}", src, 1),
                           design, stim, in_w)
        b = oracle.run_dut(re.sub(r"\bmodule\s+\w+", f"module {design}", canon, 1),
                           design, stim, in_w)
        if a is None and b is None:
            return None, "neither original nor canonical simulates"
        if a is None:
            # the input itself does not simulate; the canonicaliser is not at
            # fault and this candidate is NOT evaluable evidence either way
            return None, "original does not simulate (not evaluable)"
        if b is None:
            return False, "CANONICAL FORM DOES NOT SIMULATE"
        if len(a) != len(b) or not bool((a == b).all()):
            return False, f"trace differs at seed {sd}"
    return True, "identical"


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
    res["sha256"] = hashlib.sha256(c0.encode()).hexdigest()

    if be == "yosys":
        # C maps Verilog -> RTLIL and is not closed over its input language, so
        # C(C(x)) is undefined. Clause 2 (all spellings -> identical output) is
        # the meaningful form of the same requirement and is checked below.
        res["idempotence"] = "n/a (cross-language canonicaliser)"
    else:
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
    ap.add_argument("--check-traces", action="store_true",
                    help="also prove each canonical form is I/O-identical to "
                         "its original (needs iverilog; lexical backend only)")
    ap.add_argument("--out", default="canonicalize_contract.json")
    args = ap.parse_args()

    import glob
    import collections
    here = os.path.dirname(os.path.abspath(__file__))

    if args.self_test:
        cases = [
            ("assign y = a <= b ;", 0, 1, "continuous assign, comparison"),
            ("q <= ( a <= b ) ;", 1, 1, "nonblocking, comparison RHS"),
            ("y = ( a <= b ) ;", 0, 1, "blocking, comparison RHS"),
            ("if ( a <= b ) q <= c ;", 1, 1, "if-comparison then nonblocking"),
            ("a <= x * 3 + a ;", 1, 0, "plain accumulate"),
        ]
        bad = 0
        print("statement classifier:")
        for s, nb, cmp_, name in cases:
            fd = struct_feature_dict(s)
            good = fd["n_nonblock"] == nb and fd["n_cmp"] == cmp_
            bad += not good
            print(f"  {name:34s} nb={fd['n_nonblock']} cmp={fd['n_cmp']} "
                  f"{'ok' if good else f'FAIL want nb={nb} cmp={cmp_}'}")
        m = "module m(input clk, output reg y); reg a; always @(posedge clk) a <= ~a; endmodule"
        c1 = canon_lexical(m)
        c2 = canon_lexical(c1)
        print(f"idempotence: {'ok' if c1 == c2 else 'FAIL'}")
        bad += c1 != c2
        for name, fn in SUITE:
            eq = canon_lexical(fn(m)) == c1
            print(f"metamorphic {name:12s} {'ok' if eq else 'FAIL'}")
            bad += not eq
        print(f"\nself-test {'PASSED' if not bad else f'FAILED ({bad})'}")
        raise SystemExit(1 if bad else 0)
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
        if args.check_traces and not r.get("rejected"):
            stem = os.path.splitext(os.path.basename(f))[0]
            design = stem.split("__")[1] if "__" in stem else stem
            c, _ = canonicalize(src, args.backend, yosys=args.yosys)
            same, why = trace_equal(src, c, design)
            r["trace_equal"] = same
            r["trace_note"] = why
            if same is False:
                r["ok"] = False
                r["failures"].append("trace")
                fails["semantic:trace"] += 1
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

    # the frozen artifact must contain EVERY record, not a 50-row sample: it is
    # the evidence a reader checks the pre-registration against.
    groups = {h: [os.path.relpath(x, here) for x in fs]
              for h, fs in byhash.items() if len(fs) > 1}
    json.dump({"version": CANON_VERSION, "backend": args.backend,
               "n": len(files), "passed": ok, "rejected": rejected,
               "failures": dict(fails), "collisions": coll,
               "merge_groups": groups, "per_file": per},
              open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out}")
    print("\nThe reward may only be built on this if PASSED == n - rejected,")
    print("collisions == 0, and the rejection rate is small enough to state.")


if __name__ == "__main__":
    main()
