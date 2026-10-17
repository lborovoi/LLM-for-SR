import re

import pandas as pd
import copy
from typing import Any

CIW_MULTIPLE = {'C1', 'C3'}
CIW_COLUMN_NAMES = {
    'AU': 'authors',
    'TI': 'title',
    'AB': 'abstract',
    'PY': 'year',
    'SO': 'publication',
    'DI': 'doi',
}

def parse_ciw(filename: str) -> pd.DataFrame:
    with open(filename, 'rt', encoding='utf-8') as f:
        lines = f.readlines()

    rows = []
    row = {}
    last_item = None

    def insert_last_item():
        nonlocal last_item
        if not last_item:
            return
        prefix, value = last_item
        if prefix in CIW_MULTIPLE:
            if prefix not in row:
                row[prefix] = []
            row[prefix].append(value)

        else:
            if prefix in row:
                raise ValueError(f'Duplicate {prefix} in line {line_number}')
            row[prefix] = value

        last_item = None

    def finalize_row():
        nonlocal row
        if len(row) == 0:
            return
        rows.append(row)
        row = {}

    for i, line in enumerate(lines):
        line_number = i + 1
        line = line.rstrip()

        if line == 'EF':  # End file
            break

        if line in ('ER', ''):  # ER = end of record
            insert_last_item()
            finalize_row()
            continue

        if len(line) == 2:
            line += ' '  # For simplicity
        if line[2] != ' ':
            raise ValueError(f'Missing space separator at line {line_number}')
        prefix = line[:2]
        value = line[3:]
        if prefix == '  ':
            if not last_item:
                raise ValueError(f'Continuation of nothing in line {line_number}')
            last_item[1] += '\n' + value
        else:
            insert_last_item()
            last_item = [prefix, value]

    insert_last_item()
    finalize_row()

    df = pd.DataFrame(rows)
    df.rename(columns=CIW_COLUMN_NAMES, inplace=True)

    df['abstract'] = df['abstract'].str.replace('\n', ' ')
    df['title'] = df['title'].str.replace('\n', ' ')
    df['authors'] = df['authors'].str.replace('\n', '; ')

    other_columns = list(df.columns)
    column_order = list(CIW_COLUMN_NAMES.values())
    for col in column_order:
        other_columns.remove(col)
    column_order.extend(other_columns)
    df = df[column_order]

    return df


def get_doi(items: list[str]) -> str | None:
    for item in items:
        if item.endswith('[doi]'):
            return item.removesuffix('[doi]').strip()
    return None

NBIB_MULTIPLE = {'AU', 'FAU', 'AD', 'PT', 'MH', 'PHST', 'AID', 'IS', 'LID', 'OT', 'AUID', 'RN', 'OID',
                 'GR', 'CIN'}
NBIB_COLUMN_NAMES = {
    'FAU': 'authors',
    'TI': 'title',
    'AB': 'abstract',
    'DP': 'publication_date',
    'SO': 'publication',
    'MH': 'keywords',
    'PMID': 'pubmed_id',
}

def parse_nbib(filename: str) -> pd.DataFrame:
    with open(filename, 'rt', encoding='utf-8') as f:
        lines = f.readlines()

    rows = []
    row = {}
    last_item = None

    def insert_last_item():
        nonlocal last_item
        if not last_item:
            return
        prefix, value = last_item
        if prefix in NBIB_MULTIPLE:
            if prefix not in row:
                row[prefix] = []
            row[prefix].append(value)

        else:
            if prefix in row:
                raise ValueError(f'Duplicate {prefix} in line {line_number}')
            row[prefix] = value

        last_item = None

    def finalize_row():
        nonlocal row
        if not row:
            return
        for col in NBIB_MULTIPLE:
            if col not in row:
                row[col] = []
        rows.append(row)
        row = {}

    for i, line in enumerate(lines):
        line_number = i + 1
        line = line.rstrip()

        if not line:
            insert_last_item()
            finalize_row()
            continue
            
        if line[:6] == ' ' * 6:
            if not last_item:
                raise ValueError(f'Continuation of nothing in line {line_number}')
            last_item[1] += '\n' + line.strip()
            continue

        if line[4] != '-':
            raise ValueError(f'Missing hyphen separator at line {line_number}')
        insert_last_item()
        prefix = line[:4].strip()
        value = line[5:].strip()
        last_item = [prefix, value]

    insert_last_item()
    finalize_row()

    df = pd.DataFrame(rows)
    df.rename(columns=NBIB_COLUMN_NAMES, inplace=True)

    df['abstract'] = df['abstract'].str.replace('\n', ' ')
    df['title'] = df['title'].str.replace('\n', ' ')
    df['authors'] = df['authors'].transform('; '.join)
    df['year'] = df['publication_date'].str.extract(r'\b(\d{4})\b')
    df['doi'] = df['AID'].apply(get_doi)

    other_columns = list(df.columns)
    column_order = list(NBIB_COLUMN_NAMES.values()) + ['year', 'doi']
    for col in column_order:
        other_columns.remove(col)
    column_order.extend(other_columns)
    df = df[column_order]

    return df


def parse_ris(filename):
    entry_template = {'year': None, 'authors': [], 'title': None, 'abstract': None, 'journal': None}
    entry = copy.deepcopy(entry_template)
    ris_entries = []
    with open(filename, 'rt', encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        if not line.strip():
            if entry['year'] or entry['authors'] or entry['title']:
                entry['authors'] = ', '.join(entry['authors'])
                ris_entries.append(entry)
            entry = copy.deepcopy(entry_template)
            continue

        typ, text = line.split('-', 1)
        typ = typ.strip()
        text = text.strip()
        if typ == 'TI':
            entry['title'] = text
        elif typ == 'Y1':
            entry['year'] = text
        elif typ == 'AU':
            entry['authors'].append(text)
        elif typ == 'AB':
            entry['abstract'] = text
        elif typ == 'DO':
            entry['doi'] = text
        elif typ == 'UR':
            entry['url'] = text
        elif typ == 'T2':
            entry['journal'] = text
        elif typ == 'N1':
            _parse_ris_decisions(text, entry)
        # else:
        #     entry[typ] = text

    if entry['year'] or entry['authors'] or entry['title']:
        entry['authors'] = ', '.join(entry['authors'])
        ris_entries.append(entry)

    df = pd.DataFrame(ris_entries)
    df['year'] = df['year'].str.extract(r'\b(\d{4})\b').astype(int)
    df['pubmed_id'] = df['url'].str.extract(r'https://pubmed.ncbi.nlm.nih.gov/(\d+)/?')
    return df

def _parse_ris_decisions(text: str, row: dict[str, Any]) -> None:
    match = re.match(r'RAYYAN-INCLUSION:\s*{(.*?)}', text)
    if not match:
        return
    decisions = match.group(1).split(',')
    for decision in decisions:
        match = re.fullmatch(r'"(.*)"=>"(.*)"', decision.strip())
        if not match:
            continue
        name = match.group(1)
        value = match.group(2)
        bool_value: bool
        if value == 'Included':
            bool_value = True
        elif value == 'Excluded':
            bool_value = False
        else:
            raise ValueError(f'Invalid decision: {text}')
        row[f'decision_{name.lower()}'] = bool_value

def parse_bib(filename: str) -> pd.DataFrame:
    with open(filename, 'rt', encoding="utf-8") as f:
        lines = f.readlines()

    rows = []
    row = None
    info_found = False
    for i, line in enumerate(lines):
        line = line.strip()
        if not info_found and not line.startswith('@'):
            continue
        if not line:
            continue
        line_no = i + 1

        info_found = True
        if match := re.fullmatch(r'@([A-Z]+){(.+),', line):
            if row:
                raise ValueError(f'Starting new record when old record isn\'t finished in line {line_no}')
            row = {'id': match.group(2), 'record_type': match.group(1)}
        elif line == '}':
            if not row:
                raise ValueError(f'Finishing non-existent record in line {line_no}')
            rows.append(row)
            row = None
        else:
            match = re.fullmatch(r'(\w+)\s*=\s*{(.*)},?', line)
            if not match:
                raise ValueError(f'Invalid format in line {line_no}')
            if not row:
                raise ValueError(f'Adding to non-existent record in line {line_no}')
            row[match.group(1)] = match.group(2)
    if row:
        raise ValueError(f'Last record not closed.')

    return pd.DataFrame(rows)