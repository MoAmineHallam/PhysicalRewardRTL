"""Prepare a bounded, pinned FineWeb-Edu screen from a local public shard.

No network access. Exact content hashes assign entire documents to splits before
tokenization. This convenience shard is exploratory, not a representative final
benchmark; near-duplicate and benchmark contamination checks remain outstanding.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from tokenizers import Tokenizer
from .prepare_data import digest, text_hash

REVISION = '87f09149ef4734204d70ed1d046ddc9ca3f2b8f9'
SHARD = 'sample/10BT/000_00000.parquet'
SHA256 = 'b1ba7b2ce4cb5ea6ef42dca40263eabb85f37700d01693a68e9b30a31d78e871'


def assign_split(identity):
    bucket = int(identity[:16], 16) % 1000
    return 'validation' if bucket < 10 else 'test' if bucket < 20 else 'train'


def main():
    import pyarrow.parquet as pq
    p = argparse.ArgumentParser()
    p.add_argument('--parquet', required=True); p.add_argument('--tokenizer', required=True)
    p.add_argument('--tokenizer-metadata', required=True); p.add_argument('--out', required=True)
    a = p.parse_args()
    if digest(a.parquet) != SHA256:
        raise ValueError('pinned source shard SHA256 mismatch')
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    caps = dict(train=100663297, validation=1048577, test=1048577)
    tok = Tokenizer.from_file(a.tokenizer)
    eos = tok.token_to_id('<|endoftext|>')
    if eos is None or tok.get_vocab_size() != 50257:
        raise ValueError('expected GPT-2 tokenizer')
    arrays = {split: np.lib.format.open_memmap(out/f'{split}.npy', mode='w+',
                                             dtype=np.uint16, shape=(cap,)) for split, cap in caps.items()}
    counts = dict.fromkeys(caps, 0); docs = dict.fromkeys(caps, 0)
    seen = set(); duplicates = empty = row_number = 0
    with (out/'documents.jsonl').open('x', encoding='utf-8') as doclog:
        for batch in pq.ParquetFile(a.parquet).iter_batches(batch_size=128, columns=['text']):
            selected = []
            for text in batch.column(0).to_pylist():
                row_number += 1
                if not isinstance(text, str) or not text.strip():
                    empty += 1; continue
                identity = text_hash(text)
                if identity in seen:
                    duplicates += 1; continue
                seen.add(identity)
                split = assign_split(identity)
                if counts[split] < caps[split]:
                    selected.append((text, identity, split, row_number))
            encoded = tok.encode_batch([item[0] for item in selected], add_special_tokens=False)
            for (_, identity, split, row), encoding in zip(selected, encoded):
                ids = encoding.ids + [eos]
                count = min(len(ids), caps[split] - counts[split])
                if not count: continue
                start = counts[split]
                arrays[split][start:start+count] = ids[:count]
                counts[split] += count; docs[split] += 1
                doclog.write(json.dumps(dict(sha256=identity, split=split, source_row=row,
                                            start=start, tokens=count, truncated=count < len(ids)))+'\n')
            if row_number % 12800 == 0:
                print(json.dumps(dict(rows_scanned=row_number, tokens=counts)), flush=True)
            if counts == caps: break
    for arr in arrays.values(): arr.flush()
    if counts != caps: raise RuntimeError(f'insufficient source tokens: {counts}')
    manifest = dict(status='complete exploratory screen corpus', repository='HuggingFaceFW/fineweb-edu',
                    revision=REVISION, source_path=SHARD, source_sha256=SHA256,
                    source_url=f'https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu/resolve/{REVISION}/{SHARD}',
                    license='ODC-BY; see upstream dataset card for source-content terms',
                    tokenizer=json.loads(Path(a.tokenizer_metadata).read_text()),
                    tokenizer_sha256=digest(a.tokenizer), vocab=tok.get_vocab_size(), eos=eos,
                    split_policy='whitespace-normalized SHA256 first 64 bits mod 1000: 0..9 dev, 10..19 reserved test, remainder train',
                    token_policy='document tokens plus EOS, concatenated; final document per split token-capped; attention may cross EOS',
                    selection='first qualifying documents in pinned sample/10BT first shard; stop when all budgets fill',
                    rows_scanned=row_number, exact_duplicates_excluded=duplicates, empty_excluded=empty,
                    documents_sha256=digest(out/'documents.jsonl'),
                    limitations=['Not a globally random sample of FineWeb-Edu.',
                                 'Near-duplicate and external benchmark contamination not yet audited.',
                                 'Reserved test must not be used for recipe or architecture selection.'])
    for split in caps:
        manifest[split] = dict(tokens=counts[split], included_documents=docs[split],
                               token_file_sha256=digest(out/f'{split}.npy'))
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == '__main__': main()
