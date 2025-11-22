# Hacker News Stories Parser

A high-performance Go application for parsing and collecting Hacker News stories. This project maintains an auto-updating dataset of HN stories that is published to Hugging Face.

## Dataset

The parsed stories are automatically published to Hugging Face:
**https://huggingface.co/datasets/artbred/hn_stories**

The dataset is automatically updated weekly via GitHub Actions, ensuring you always have access to the latest high-quality Hacker News stories.

## Filter Criteria

Only stories with a **score >= 10** are included in the dataset. This ensures the dataset contains stories that have received meaningful community engagement.

## Features

- High-performance concurrent parsing with rate limiting
- Checkpoint/resume support for long-running operations
- Incremental updates from existing datasets
- Automatic dataset publishing to Hugging Face
- Weekly automated updates via GitHub Actions

## Basic Usage

### Build

```bash
go build -o hn_parser main.go
```

### Fetch Stories

Fetch a specific number of stories (with score >= 10):

```bash
./hn_parser -output stories.jsonl -stories 10000 -min-score 10
```

### Incremental Update

Update from an existing dataset file:

```bash
./hn_parser -update-from-file existing_stories.jsonl -min-score 10
```

Or update from a URL:

```bash
./hn_parser -update-from-url https://example.com/stories.jsonl -min-score 10
```

### Command Line Options

- `-output`: Output JSONL file path (default: auto-generated)
- `-stories`: Number of stories to download (0 = incremental update)
- `-min-score`: Minimum score filter (default: 1, dataset uses 10)
- `-min-descendants`: Minimum descendants filter (default: 0)
- `-concurrent`: Max concurrent requests (default: 100)
- `-rps`: Requests per second limit (default: 200)
- `-update-from-file`: Update incrementally from existing JSONL file
- `-update-from-url`: Update incrementally from JSONL file at URL
- `-resume-id`: Resume from specific ID (overrides checkpoint)
- `-stop-at-id`: Stop processing when this ID is reached

## Output Format

The parser outputs JSONL (JSON Lines) format, where each line is a JSON object representing a story:

```json
{"id": 12345678, "title": "Story Title", "url": "https://example.com", "type": "story", "by": "username", "time": 1234567890, "score": 15, "descendants": 5, "kids": [12345679, 12345680]}
```

## Automated Updates

The dataset is automatically updated every week via GitHub Actions. The update process:

1. Loads the existing dataset from Hugging Face
2. Fetches new stories since the last update
3. Merges and deduplicates the data
4. Publishes the updated dataset to Hugging Face
