import itertools
import pandas as pd
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Should be present in itertools
def batched(iterable, n):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    iterator = iter(iterable)
    while batch := tuple(itertools.islice(iterator, n)):
        yield batch


def is_missing(series: pd.Series) -> pd.Series:
    return series.isna() | (series == '')

def list_files(directory: str, extension: str) -> list[str]:
    paths = []
    for current_dir, subdirs, files in os.walk(directory):
        for file in files:
            path = os.path.join(current_dir, file)
            if path.endswith(extension):
                paths.append(path)

    return paths

def run_in_parallel(tasks, n_workers=8):
    responses = []

    with ThreadPoolExecutor(max_workers=n_workers) as executor:
        futures = [executor.submit(task) for task in tasks]

        for future in tqdm(futures):
            responses.append(future.result())

    return responses

