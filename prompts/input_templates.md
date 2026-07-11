# Input templates

## Per-article block

The article index starts at 1.

```
## ARTICLE {index}

TITLE: {title_or_<Missing>}
AUTHORS: {authors_or_<Missing>}
PUBLISHED ON: {year_or_<Missing>}
ABSTRACT:
{abstract_or_<Missing>}
```

After all article blocks, the selected review criteria were appended verbatim.
For title-only screening, the abstract field was forced to `<Missing>`. For
title/abstract screening, the abstract was supplied when available.

