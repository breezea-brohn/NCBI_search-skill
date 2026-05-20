# NCBI Search Skill

A biomedical research tool that searches NCBI databases for gene information and scientific literature.

## Features

- **Gene Lookup** — Query NCBI Gene database for official gene summaries, chromosomal locations, and aliases
- **PubMed Search** — Retrieve scientific literature with structured metadata including MeSH terms
- **Agentic Workflow** — Designed for AI agents to explore biological questions step by step

## Quick Start

```bash
# Gene information lookup (defaults to human)
python scripts/pubmed_search.py gene "CSF2"

# Specify species
python scripts/pubmed_search.py gene "Tp53" --species "mouse"

# Search PubMed literature
python scripts/pubmed_search.py search "CSF2 AND lung cancer AND prognosis" --max 5
```

## Output Examples

**Gene lookup returns:**
- Gene ID, symbol, description
- Chromosomal location
- Aliases
- Official NCBI summary

**Literature search returns:**
- PMID, title, year
- Abstract
- MeSH (Medical Subject Headings) terms

## Requirements

- Python 3.x
- No external dependencies (uses NCBI E-utilities API)

## License

MIT License
