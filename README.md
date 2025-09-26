# LLM for Code Recommendation

A research project that leverages Large Language Models (LLMs) to provide intelligent code recommendations for fixing software vulnerabilities. The system implements four different retrieval patterns to enhance the accuracy and relevance of vulnerability fix recommendations.

## Overview

This project focuses on using LLMs to recommend fixes for vulnerable code by analyzing Common Weakness Enumeration (CWE) and Common Vulnerabilities and Exposures (CVE) data. The system processes vulnerability datasets, implements multiple retrieval strategies, and generates contextual recommendations for fixing security issues in code.

## Features

- **Multi-Pattern Retrieval**: Implements four distinct retrieval patterns for different use cases
- **Dataset Preprocessing**: Comprehensive data cleaning, deduplication, and stratified splitting
- **Vulnerability Analysis**: Supports both BigVul and CVEfixes datasets
- **Evaluation Framework**: Detailed rubrics for assessing recommendation quality
- **Modular Architecture**: Clean separation of concerns with reusable components

## Installation

This project requires Python 3.10 or higher. We recommend using `uv` for dependency management.

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager

### Install Dependencies

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd llm-for-code-recommendation

# Install dependencies using uv
uv sync
```

### Alternative Installation

If you prefer using pip:

```bash
pip install -e .
```

## Project Structure

```
llm-for-code-recommendation/
├── data/                           # All data processing outputs
│   ├── cvefixes_kb.csv            # CVEfixes knowledge base
│   ├── cvefixes_test.csv          # CVEfixes test set
│   └── cvefixes_split_stats.txt   # Dataset statistics
├── patterns/                       # Knowledge base creation notebooks
│   ├── vanilla/                   # Basic single-context pattern
│   ├── segmented-context/         # Context segmentation pattern
│   ├── metadata-embedding/        # Individual field embedding
│   └── metadata-driven-retrieval/ # Metadata-enhanced retrieval
├── prompts/                       # LLM prompt templates
│   ├── code-fix-prompt.txt
│   ├── recommendation-prompt.txt
│   └── vul-extraction-prompt.txt
├── evaluation criteria/           # Evaluation rubrics and metrics
├── output/                        # All outputs from script.ipynb
├── script.ipynb                   # End-to-end workflow (configurable dataset, models, evaluation)
├── bias.ipynb                     # Tests GPT-4o judge bias using Llama perturbations
├── preprocessing.py               # Dataset preprocessing pipeline
├── main.py                        # Basic entry point
└── pyproject.toml                # Project configuration and dependencies
```

## Usage

### 1. Dataset Preprocessing

First, preprocess vulnerability datasets with deduplication and stratified splitting:

```bash
# Process BigVul dataset
python preprocessing.py bigvul bigvul_sample.csv --output-dir data --test-size 0.2

# Process CVEfixes dataset
python preprocessing.py cvefixes cvefixes_sample.csv --output-dir data --test-size 0.2
```

**Command Line Options:**

```bash
python preprocessing.py <dataset> <input_file> [options]

Arguments:
  dataset                 Dataset to process (bigvul or cvefixes)
  input_file             Path to input CSV file

Options:
  --output-dir DIR       Output directory (default: data)
  --test-size FLOAT      Test set size ratio (default: 0.2)
  --random-state INT     Random state for reproducibility (default: 42)
  --similarity-threshold FLOAT  Similarity threshold for deduplication (default: 0.95)
```

### 2. Build Knowledge Base

Use the pattern notebooks to create vector databases for each retrieval approach. Run the notebooks in the `patterns/` directory:

- `patterns/vanilla/script.ipynb`
- `patterns/segmented-context/script.ipynb`
- `patterns/metadata-embedding/script.ipynb`
- `patterns/metadata-driven-retrieval/script.ipynb`

### 3. Run End-to-End Workflow

Execute the main workflow using `script.ipynb`. This contains the e2e flow using LLM judge metrics.

**Configurable Parameters in script.ipynb:**

- Dataset file name
- Vector database index to use
- LLM models (OpenAI, Groq, etc.)
- Evaluation criteria and rubrics
- Context window settings
- Token limits

### 4. Bias Testing (Optional)

Test for LLM judge bias using `bias.ipynb`. This notebook perturbs GPT-4o's recommendations using Llama to test if the GPT-4o judge shows bias. After obtaining the recommendation file, you can continue after the `script.ipynb` portion that generates these files.

## Evaluation Criteria

The system uses a comprehensive 5-point rubric to evaluate recommendation quality across five dimensions:

| Criteria                   | Description                                                  |
| -------------------------- | ------------------------------------------------------------ |
| **Relevance**              | How applicable the recommendation is to the identified issue |
| **Completeness**           | Thoroughness and comprehensiveness of the recommendation     |
| **Correctness**            | Accuracy and reliability of the information provided         |
| **Id. of Vulnerable Code** | Specificity in identifying the vulnerable code sections      |
| **Code Guidance**          | Quality and helpfulness of provided code snippets            |

Each criterion is scored from 1 (poor) to 5 (excellent), providing a detailed assessment framework.

## Dependencies

Key dependencies include:

- **LangChain**: LLM framework and integrations
- **Pinecone**: Vector database for embeddings
- **Transformers**: Hugging Face model support
- **Pandas**: Data manipulation and analysis
- **Scikit-learn**: Machine learning utilities
- **Jupyter**: Interactive development environment

See `pyproject.toml` for the complete dependency list.
