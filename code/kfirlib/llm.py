import re
import pandas as pd
import numpy as np
from tqdm import tqdm
import requests
import json
import base64
import mimetypes
from kfirlib import prompts

from .util import *

_KEY = 'YOUR_API_KEY'

GPT_FULL = 'gpt-4o'
GPT_MINI = 'gpt-4.1-mini'
GEMINI_3_FLASH = 'google/gemini-3-flash-preview'

def query(*, model: str, instructions: str, input: str, filenames=None) -> str:
    filenames = filenames or []
    user_content = [{"type": "text", "text": input}]
    for filename in filenames:
        with open(filename, 'rb') as f:
            file_content = f.read()
        user_content.append(
            {
                "type": "file",
                "file": {
                    "filename": filename,
                    "file_data": make_data_url(filename, file_content),  # note: docs show this snake_case key in the Python example
                },
            },
        )

    response = requests.post(
        url='https://openrouter.ai/api/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {_KEY}',
        },
        data=json.dumps({
            'model': model,  # Optional
            'messages': [
                {'role': 'system', 'content': instructions},
                {'role': 'user', 'content': user_content},
            ]
        })
    )

    if not response.ok:
        try:
            err_dict = json.loads(response.text)
            error_message = err_dict["error"]["message"]
        except:
            response.raise_for_status()
        raise ValueError(f'Error calling {model}: {error_message}')
    return response.json()['choices'][0]['message']['content']


def make_data_url(file_name: str, file_content: bytes) -> str:
    mime_type, _ = mimetypes.guess_type(file_name)

    if mime_type is None:
        mime_type = "application/octet-stream"

    b64 = base64.b64encode(file_content).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def _parse_eligibility_output(
        output: str,
        article_count: int,
) -> pd.DataFrame:
    results = []
    cur_result = None
    next_index = 1
    for line in output.splitlines():
        if not line.strip() or line.strip() == '```':
            continue

        single_article_match = re.search(r'ARTICLE\s+(\d+)\s*$', line)
        multi_article_match = re.search(r'ARTICLES?\s+(\d+)\s*(?:-|to|to ARTICLE|&)\s*(\d+)\s*$', line)
        if single_article_match or multi_article_match:
            if next_index > article_count:
                break

            if single_article_match:
                first_index = int(single_article_match.group(1))
                last_index = first_index
            else:
                first_index = int(multi_article_match.group(1))
                last_index = int(multi_article_match.group(2))

            if first_index != next_index:
                raise ValueError(f'Wrong article: line "{line}", next index  {next_index}')
            next_index = last_index + 1

            cur_result = {'reasoning': '', 'decision': np.nan}
            for _ in range(first_index, last_index + 1):
                results.append(cur_result)

        elif match := re.search(r'\b(IN|EX)CLUDE\b', line):
            cur_result['decision'] = (match.group() == 'INCLUDE')
        elif 'Final decisions:' in line:
            break
        else:
            if cur_result:
                cur_result['reasoning'] += line + '\n'
            else:
                print(f'WARNING: Line outside article: "{line}"')

    return pd.DataFrame(results)


def _fix_missing(val):
    if (isinstance(val, float) and np.isnan(val)) or not val:
        return '<Missing>'
    return val

def _format_article(index, article):
    return f'''
## ARTICLE {index + 1}

TITLE: {_fix_missing(article.title)}
AUTHORS: {_fix_missing(article.authors)}
PUBLISHED ON: {_fix_missing(article.year)}
ABSTRACT: 
{_fix_missing(article.abstract)}
'''


def _make_prompt(batch, criteria):
    parts = []
    for i, item in enumerate(batch):
        parts.append(_format_article(i, item))
    parts.append(criteria)
    return '\n'.join(parts)


def _validate_columns(df: pd.DataFrame) -> pd.DataFrame:
    expected_columns = ['title', 'authors', 'year', 'abstract']
    renamings = {}
    for column in expected_columns:
        cap_column = column.capitalize()
        if column in df.columns:
            pass
        elif cap_column in df.columns:
            renamings[cap_column] = column
        else:
            raise ValueError(f'The following columns are expected: {expected_columns}. {column} is missing.')
    return df.rename(columns=renamings)


def _make_bad_result(n: int) -> pd.DataFrame:
    return pd.DataFrame({'decision': [np.nan] * n, 'reasoning': [np.nan] * n})


def check_eligibility(
        articles_df: pd.DataFrame,
        *,
        system_prompt: str,
        criteria: str,
        debug: bool = False,
        model: str,
        batch_size: int = 50,
        show_progress: bool | None = None,
        suffix: str = '',
        use_abstract=True,
) -> pd.DataFrame:
    in_df = _validate_columns(articles_df)
    if not use_abstract:
        in_df = in_df.drop(['abstract'], axis=1, errors='ignore')
        in_df['abstract'] = ''

    batches = list(batched(in_df.itertuples(), batch_size))
    if show_progress is None:
        show_progress = len(batches) > 1
    if show_progress:
        batches = tqdm(batches)

    batch_responses = []
    for i, batch in enumerate(batches):
        response = query(model=model, instructions=system_prompt, input=_make_prompt(batch, criteria))
        try:
            df = _parse_eligibility_output(response, len(batch))
        except ValueError as v:
            print(f'Error in batch {i}: {v}')
            if debug:
                print('----------------------')
                print(response)
                print('----------------------')
            df = _make_bad_result(len(batch))
        if len(df) != len(batch):
            print(f'Wrong length: needed {len(batch)} but got {len(df)} in batch {i}.')
            df = _make_bad_result(len(batch))
            if debug:
                print('----------------------')
                print(response)
                print('----------------------')
        batch_responses.append(df)

    all_results = pd.concat(batch_responses, axis=0)
    all_results['reasoning'] = all_results['reasoning'].str.replace('```', '').str.strip()
    all_results.index = articles_df.index
    if suffix:
        all_results.rename(columns={'reasoning': 'reasoning' + suffix, 'decision': 'decision' + suffix},
                           inplace=True)

    articles_df = articles_df.drop(all_results.columns, axis=1, errors='ignore')
    articles_with_decisions = pd.concat([articles_df, all_results], axis=1)
    return articles_with_decisions


def fill_in_eligibility(
        articles_df: pd.DataFrame,
        *,
        system_prompt: str = prompts.SYSTEM_PROMPT,
        criteria: str,
        model: str,
        debug: bool = True,
        batch_size: int = 50,
        show_progress: bool | None = None,
) -> None:
    missing_values = is_missing(articles_df.decision) | is_missing(articles_df.reasoning)
    missing_index = missing_values[missing_values].index
    missing_df = articles_df.loc[missing_index, :]

    decisions_df = check_eligibility(
        missing_df,
        system_prompt=system_prompt,
        criteria=criteria,
        model=model,
        batch_size=batch_size,
        show_progress=show_progress,
        debug=debug,
    )

    articles_df.loc[missing_index, ['decision', 'reasoning']] = decisions_df.loc[:, ['decision', 'reasoning']]

