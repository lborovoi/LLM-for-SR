from kfirlib import llm, prompts, util
from typing import Any
import pandas as pd
from tqdm import tqdm

DECISION_DICT = {'INCLUDE': True, 'EXCLUDE': False}
EXTRACTED_KEYS = ['title', 'reasoning', 'decision', 'authors', 'doi', 'pmid']
UPPER_CASE_KEYS = {key.upper() for key in EXTRACTED_KEYS}

def _parse_pdf_response(response: str) -> list[dict[str, Any]]:
    items = []
    current_type = None

    for line in response.splitlines():
        line = line.strip()
        if not line or line in {'```', '---'}:
            continue
        if line in UPPER_CASE_KEYS:
            current_type = line
            if line == 'TITLE':
                items.append({key: '' for key in EXTRACTED_KEYS})
            continue

        if not current_type:
            raise ValueError(f'This line has no key to assign to: "{line}"')
        key = current_type.lower()
        _add_info(items[-1], key, line)

        if current_type in ('DECISION', 'DOI'):
            current_type = ''

    for i, item in enumerate(items):
        if not all(item[key] for key in EXTRACTED_KEYS):
            raise ValueError(f'Bad item {i}: {item}')
        decision = item['decision']
        if decision not in DECISION_DICT:
            raise ValueError(f'Invalid decision in item {i}: {decision}')
        item['decision'] = DECISION_DICT[decision]

    titles = [item['title'] for item in items]
    if len(set(titles)) < len(titles):
        raise ValueError(f'Titles are not unique: {titles}')

    return items


def _add_info(item, key, line):
    current = item[key]
    if current:
        item[key] = '\n'.join([current, line])
    else:
        item[key] = line


class EvalProcess:
    def __init__(self, paths: list[str], model: str, criteria: str):
        self.paths = paths
        self.model = model
        self.criteria = criteria
        self.items = [{'filename': path} for path in paths]

    def evaluate(self) -> pd.DataFrame:
        for batch_size in [5, 3, 1]:
            print(f'Running batches of size {batch_size}')
            self._run_on_missing_items(batch_size)
        return pd.DataFrame(self.items)

    def process_batch(self, filenames, batch_ind):
        output = None
        try:
            output = llm.query(model=self.model, instructions=prompts.PDF_SYSTEM_PROMPT, input=self.criteria, filenames=filenames)
        except KeyboardInterrupt as e:
            raise
        except BaseException as e:
            print(f'Error: {type(e)}, {e}', end='\r')
            print('Current files:', *filenames, sep='\n', end='\r')
            return []

        try:
            items = _parse_pdf_response(output)
        except Exception as e:
            print(f'Error in batch {batch_ind}: {e}\r')
            return []
        if len(items) != len(filenames):
            print(f'Batch {batch_ind}: Expected {len(filenames)} results but got {len(items)}.\r')
            # print(output, end='\r')
            return []
        return items

    def _run_on_missing_items(self, batch_size: int) -> None:
        to_process = [item for item in self.items if 'title' not in item]
        if not to_process:
            print('Nothing to run on')
            return
        print(f'Running on {len(to_process)} articles')

        batches = list(util.batched(to_process, batch_size))
        batch_tasks = []
        for ind, batch in enumerate(batches):
            filenames = [item['filename'] for item in batch]
            batch_tasks.append(lambda filenames=filenames, ind=ind: self.process_batch(filenames, ind))

        outputs = util.run_in_parallel(batch_tasks)

        missing_items = 0
        updated_items = 0

        for i, (output, batch) in enumerate(zip(outputs, batches)):
            if len(output) != len(batch):
                missing_items += len(batch)
                if len(output) != 0:
                    print(f'Batch {i} has only {len(output)} items in its output.')
                continue
            for item, result in zip(batch, output):
                item.update(result)
            updated_items += len(batch)

        print(f'Updated {updated_items} items, missing {missing_items} items.')