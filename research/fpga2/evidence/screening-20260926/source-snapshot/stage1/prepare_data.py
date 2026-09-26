"""Audit existing JSONL files and prepare a bounded, deduplicated pilot corpus.

The input provenance is local C4 from the earlier project, not a newly verified
upstream C4 revision. Never use this development corpus as a fresh final test set.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from tokenizers import Tokenizer


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def text_hash(text):
    return hashlib.sha256(' '.join(text.split()).encode('utf8')).hexdigest()


def records(path, audit, allow_truncated_tail):
    size = Path(path).stat().st_size
    with open(path, 'rb') as f:
        line = 0
        while True:
            raw = f.readline()
            if not raw:
                break
            line += 1
            try:
                obj = json.loads(raw)
            except (ValueError, UnicodeDecodeError):
                if allow_truncated_tail and f.tell() == size and not raw.endswith(b'\n'):
                    audit['excluded_truncated_tail_line'] = line
                    audit['excluded_truncated_tail_bytes'] = len(raw)
                    break
                raise ValueError(f'malformed JSON at line {line} in {path}')
            if not isinstance(obj.get('text'), str):
                raise ValueError(f'non-text record at line {line}')
            audit['complete_records'] = line
            yield obj['text']


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--train', required=True); p.add_argument('--validation', required=True)
    p.add_argument('--tokenizer', required=True); p.add_argument('--out', required=True)
    p.add_argument('--train-tokens', type=int, default=8388608)
    p.add_argument('--validation-tokens', type=int, default=262144)
    p.add_argument('--allow-truncated-tail', action='store_true')
    a = p.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    tok = Tokenizer.from_file(a.tokenizer)
    eos = tok.token_to_id('<|endoftext|>')
    if eos is None or tok.get_vocab_size() > 65536:
        raise ValueError('requires GPT-2 EOS and uint16-compatible vocabulary')
    manifest = {'status': 'development pilot only', 'provenance': 'existing locally labeled C4; upstream revision unverified',
                'tokenizer_sha256': digest(a.tokenizer), 'vocab': tok.get_vocab_size(), 'eos': eos,
                'policy': 'whitespace-normalized exact document dedup; EOS-concatenated token stream; context resets at sampled windows; no document-isolated attention',
                'selection': 'first unique records in existing file order, token-capped; not random corpus sampling',
                'train': {'sha256': digest(a.train)}, 'validation': {'sha256': digest(a.validation)}}
    heldout = set(); val_tokens = []; val_used = 0
    for text in records(a.validation, manifest['validation'], a.allow_truncated_tail):
        h = text_hash(text)
        if h in heldout or not text.strip():
            continue
        heldout.add(h)
        if len(val_tokens) < a.validation_tokens:
            val_tokens.extend(tok.encode(text, add_special_tokens=False).ids + [eos]); val_used += 1
    # Audit the entire source even after filling the token budget, so a late
    # malformed record or train/validation duplicate is not silently missed.
    seen = set(); train_tokens = []; overlaps = 0; duplicates = 0; train_used = 0
    for text in records(a.train, manifest['train'], a.allow_truncated_tail):
        if not text.strip():
            continue
        h = text_hash(text)
        if h in heldout:
            overlaps += 1; continue
        if h in seen:
            duplicates += 1; continue
        seen.add(h)
        if len(train_tokens) < a.train_tokens:
            train_tokens.extend(tok.encode(text, add_special_tokens=False).ids + [eos]); train_used += 1
    for split, ids, cap, docs in [('train', train_tokens, a.train_tokens, train_used),
                                 ('validation', val_tokens, a.validation_tokens, val_used)]:
        arr = np.asarray(ids[:cap], dtype=np.uint16)
        if len(arr) < cap:
            raise ValueError(f'insufficient {split} tokens: {len(arr)} < {cap}')
        path = out / f'{split}.npy'; np.save(path, arr)
        manifest[split].update(tokens=len(arr), included_documents=docs,
                               token_file_sha256=digest(path))
    manifest.update(train_validation_exact_overlaps_excluded=overlaps,
                    train_internal_duplicates_excluded=duplicates,
                    all_validation_unique_documents=len(heldout))
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__':
    main()
