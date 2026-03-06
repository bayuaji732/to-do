# Book Recommender

A semantic book recommendation system built with LangChain, Gradio, and OpenAI embeddings.

## Overview

This project uses AI-powered semantic search to recommend books based on user descriptions. Users can filter recommendations by category and emotional tone (Happy, Surprising, Angry, Suspenseful, Sad).

## Features

- **Semantic Search**: Uses OpenAI embeddings to understand book descriptions and match user queries
- **Category Filtering**: Filter recommendations by book category
- **Emotional Tone**: Select the emotional tone you want in your book recommendations
- **Visual Interface**: Clean Gradio dashboard with book cover thumbnails and descriptions

## Dataset

7k Books: https://www.kaggle.com/datasets/dylanjcastillo/7k-books-with-metadata

## Requirements

- Python 3.8+
- OpenAI API key
- HuggingFace token
- Dependencies listed in `pyproject.toml` or `requirements.txt`

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd book-recommender
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Create a `.env` file and add your OpenAI API key and HF token:
   ```
   OPENAI_API_KEY=your_api_key_here
   HF_TOKEN=your_hf_token_here
   ```

4. Ensure you have the required data files:
   - `books_with_emotions.csv`
   - `tagged_description.txt`

## Usage

Run the Gradio dashboard:

```bash
uv run gradio-dashboard.py
```

Then open your browser to the URL displayed in the terminal (typically `http://localhost:7860`).

1. Enter a book description in the textbox
2. Select a category (optional)
3. Select an emotional tone (optional)
4. Click "Find recommendations"