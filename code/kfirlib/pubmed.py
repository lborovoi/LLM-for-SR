from pymed import PubMed
import pandas as pd
from tqdm import tqdm

_PUBMED = PubMed(tool='BioC', email="you@example.org")

# All fields: ['pubmed_id', 'title', 'abstract', 'keywords', 'journal', 'publication_date', 'authors', 'methods', 'conclusions', 'results', 'copyrights', 'doi', 'xml']

def query(query_string: str, *, max_results: int = 500) -> pd.DataFrame:
    results = _PUBMED.query(query_string, max_results=max_results)
    rows = []
    for result in results:
        row = {}
        for field in ['title', 'publication_date', 'abstract']:
            row[field] = getattr(result, field)
        row['authors'] = ', '.join(
            f'{author["lastname"]}, {author["initials"]}.' for author in result.authors)
        row['pubmed_id'] = result.pubmed_id.splitlines()[0]
        row['keywords'] = ', '.join(result.keywords) if hasattr(result, 'keywords') else ''
        row['doi'] = result.doi
        rows.append(row)
    return pd.DataFrame(rows)


BATCH_SIZE = 100

def add_lines_by_pubmed_id(df: pd.DataFrame, pmid_col: str) -> pd.DataFrame:
    parts = []
    # Keep the complete identifier list separate from each batch. Reassigning
    # `ids` to a slice here previously made every batch after the first empty.
    all_ids = df[pmid_col].dropna().astype(int).drop_duplicates().tolist()
    starts = list(range(0, len(all_ids), BATCH_SIZE))
    for start in tqdm(starts):
        batch_ids = all_ids[start:start + BATCH_SIZE]
        query_str = ' OR '.join(f'{pmid}[PMID]' for pmid in batch_ids)
        part = query(query_str, max_results=BATCH_SIZE * 2)
        if not part.empty:
            parts.append(part)
    if parts:
        all_pubmed_results = pd.concat(parts, axis=0, ignore_index=True)
    else:
        all_pubmed_results = pd.DataFrame(columns=[
            'title', 'publication_date', 'abstract', 'authors',
            'pubmed_id', 'keywords', 'doi',
        ])
    all_pubmed_results['pubmed_id'] = all_pubmed_results['pubmed_id'].astype(df[pmid_col].dtype)
    return pd.merge(
        df, all_pubmed_results, left_on=pmid_col, right_on='pubmed_id',
        how='left', sort=False, validate='many_to_one',
    )
