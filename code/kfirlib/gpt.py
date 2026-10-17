# This is the old version. The new version is llm.py.

from openai import OpenAI
import re
import pandas as pd
import numpy as np
from tqdm import tqdm

from .util import *

KFIR_KEY = 'YOUR_API_KEY'
PERSONAL_KEY = 'YOUR_API_KEY'
_CLIENT = OpenAI(
    api_key=KFIR_KEY,
)

def use_key(key):
    _CLIENT = OpenAI(api_key=key)

def get_client():
    return _CLIENT

class Models:
    FULL = 'gpt-4o'
    MINI = 'gpt-4.1-mini'


SYSTEM_PROMPT = '''
You are a scientist. You are given a set of inclusion and exclusion criteria and a list of articles. You must decide
whether to include each article and explain why. 
Try your best even if the abstract is missing.

The format should be as follows:

```
## ARTICLE 1

<reasoning>

INCLUDE or EXCLUDE
```

You must make a decision for **each** input and write it only once.
'''


PAUL_CRITERIA = '''
## INCLUSION CRITERIA

- Study type: Observational studies published in peer-reviewed literature.
- Participants: Individuals tested for SARS-CoV-2 by serological or molecular tests, with or without control groups.
- Outcomes: Studies reporting physical and/or mental health symptoms, symptom clusters, new onset symptoms, or ongoing symptoms following initial SARS-CoV-2 infection.
- Timeframe: No restriction on the time elapsed between infection and symptom reporting, as long as participants had a prior SARS-CoV-2 infection.
- Language: Only studies published in English.
- Publication date: Studies published between January 2020 and August 2022.
- Geographic location: No restrictions applied.
'''

JUMALAH_CRITERIA = '''
## INCLUSION CRITERIA
Studies that focus on barriers, enablers, or facilitators of MMR or HPV vaccination
Geography- global, Conducted in developed countries (mid-to-high income countries)
Study Design: Randomized controlled trials (RCTs), quasi-experimental, ecological, or observational cohort studies•	Study Design: Randomized controlled trials (RCTs), quasi-experimental, ecological, or observational cohort studies
Peer reviewed articles
Articles published in English
Articles published since 2010
Population: children, adolescents, parents, health care workers in mid-to-high income countries
Excluding: interventions, studies from U.S. (case by case- depending on population looked at), studies with health systems very different
'''

NATALIE_CRITERIA = '''
## INCLUSION CRITERIA (Natalie):
Studies published in peer-reviewed journals
Studies conducted on Israeli population
Report on prevalence of:
Asthma
Atopic dermatitis
Food allergy
Allergic rhinitis
Provide data by age group, population subgroup, geographic region, or time period
Study types: Observational studies (cross-sectional, cohort, registry-based)
Published in English or Hebrew
Indexed in PubMed, Scopus or Web of Science
Excluding: Case reports, editorials, or reviews (unless they cite relevant primary data)
'''


def query(*, model: str, instructions: str, input: str) -> str:
    response = _CLIENT.responses.create(
        model=model,
        instructions=instructions,
        input=input)
    return response.output_text


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
        system_prompt: str = SYSTEM_PROMPT,
        criteria: str,
        debug: bool = False,
        model: str = Models.MINI,
        batch_size: int = 50,
        show_progress: bool | None = None,
) -> pd.DataFrame:
    articles_df = _validate_columns(articles_df)
    batches = list(batched(articles_df.itertuples(), batch_size))
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
    all_results.index = articles_df.index
    articles_df = articles_df.drop(['decision', 'reasoning'], axis=1, errors='ignore')
    articles_with_decisions = pd.concat([articles_df, all_results], axis=1)
    articles_with_decisions['reasoning'] = articles_with_decisions['reasoning'].str.replace('```', '').str.strip()
    return articles_with_decisions


def fill_in_eligibility(
        articles_df: pd.DataFrame,
        *,
        system_prompt: str = SYSTEM_PROMPT,
        criteria: str,
        model: str = Models.MINI,
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

