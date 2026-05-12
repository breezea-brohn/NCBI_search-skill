---
name: pubmed-search
description: Search NCBI PubMed database for biomedical literature (with MeSH terms) and NCBI Gene database for official gene summaries.
metadata: {"openclaw":{"requires":{"bins":["python"]}}}
---

# NCBI PubMed & Gene Search

A comprehensive biomedical research tool that interacts with NCBI databases. It can fetch official gene summaries and retrieve scientific literature with structured metadata.

## When to Use

- When the user asks for the function, aliases, or background of a specific gene.
- When the user needs to find scientific articles, medical research, clinical studies, or verify biological pathways.
- When the user is doing literature review on cancer prognosis, gene interactions, or bioinformatics.

---

## Commands

### 1. Gene Information Lookup (`gene`)

Query the NCBI Gene database to get official summaries, chromosomal locations, and aliases for a specific gene. **Always use this first if the user mentions a gene you are not fully familiar with.**

```bash
python scripts/pubmed_search.py gene "<symbol>" --species "<species>"
```

**Examples:**
```bash
# Basic gene lookup (defaults to human)
python scripts/pubmed_search.py gene "CSF2"

# Specify species
python scripts/pubmed_search.py gene "Tp53" --species "mouse"
```

**Expected JSON Output:**
```json
{
  "success": true,
  "found": true,
  "data": {
    "gene_id": "1438",
    "symbol": "CSF2",
    "description": "colony stimulating factor 2",
    "location": "5q31.1",
    "aliases": "CSF, GMCSF",
    "summary": "The protein encoded by this gene is a cytokine that controls the production, differentiation, and function of granulocytes and macrophages..."
  }
}
```

### 2. Literature Search (`search`)

Search the PubMed database for biomedical literature. Returns paper metadata including PMID, title, year, abstract, and **MeSH (Medical Subject Headings) terms**.

```bash
python scripts/pubmed_search.py search "<query>" --max <number>
```

**Query Syntax Tips:**
- Use `AND`, `OR`, `NOT` for Boolean logic.
- Use quotes for exact phrases.

**Examples:**
```bash
# Search with precise keywords
python scripts/pubmed_search.py search "CSF2 AND Lung Squamous Cell Carcinoma AND prognosis" --max 5
```

**Expected JSON Output:**
```json
{
  "success": true,
  "query": "...",
  "resultCount": 1,
  "results": [
    {
      "pmid": "12345678",
      "year": "2023",
      "title": "Prognostic value of CSF2 in lung cancer.",
      "mesh_terms": ["Carcinoma, Squamous Cell", "Colony-Stimulating Factor 2", "Prognosis"],
      "abstract": "Abstract text..."
    }
  ]
}
```

---

## Agentic Workflow (How to use these tools)

When tasked with a complex biological question (e.g., "What is the role of CSF2 in lung cancer prognosis?"):
1. **Explore context:** Run the `gene` command first to understand what CSF2 is and get its aliases (e.g., GMCSF).
2. **Retrieve evidence:** Run the `search` command using the gene symbol and its aliases combined with the disease context.
3. **Analyze:** Read the returned `abstract` and `mesh_terms`. The `mesh_terms` provide highly accurate, human-annotated keywords that summarize the paper's true focus.
4. **Synthesize:** Present a clear, structured Markdown response to the user based STRICTLY on the retrieved data. Do not hallucinate findings.

## Requirements

- Python 3.x

