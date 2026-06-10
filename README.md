# Game Insight Pipeline

A Python ETL pipeline that extracts video game data from the RAWG API, stores it in PostgreSQL, and generates a genre-based analytics report in CSV format.

## Overview

This project demonstrates a complete ETL workflow:

1. Extracts game data from the RAWG API
2. Transforms and cleans the data using Pandas
3. Loads the data into PostgreSQL
4. Generates a CSV report with genre-level analytics

The pipeline fetches 50 games and produces a summary report containing:

* Genre name
* Number of games in the genre
* Average rating
* Average playtime

The report is sorted by average rating.

---

## Tech Stack

* Python
* Pandas
* PostgreSQL
* Psycopg
* Requests
* Python Logging
* RAWG API

---

## Project Structure

```text
game-insight-pipeline/
│
├── src/
│   └── pipeline.py
│
├── outputs/
│   └── genre_summary.csv
│
├── logs/
│   └── pipeline.log
│
├── .env
├── requirements.txt
└── README.md
```

---

## ETL Workflow

```text
RAWG API
    ↓
Extract
    ↓
Transform (Pandas)
    ↓
Load (PostgreSQL)
    ↓
Genre Summary Report (CSV)
```

---

## Database Schema

The pipeline creates a table named `games`.

| Column        | Type    |
| ------------- | ------- |
| rawg_id       | INTEGER |
| name          | TEXT    |
| rating        | FLOAT   |
| released      | DATE    |
| genres        | TEXT    |
| platforms     | TEXT    |
| playtime      | INTEGER |
| ratings_count | INTEGER |

### Database Schema

![Database Schema](assets/database_schema.png)

### Sample Data

![Sample Data](assets/sample_data.png)

---

## Genre Summary Report

The generated report is saved to:

```text
outputs/genre_summary.csv
```

### Sample Report

![Genre Summary](assets/genre_summary.png)

---

## Setup

Create a `.env` file in the project root:

```env
RAWG_API_KEY=your_rawg_api_key

DB_HOST=localhost
DB_PORT=5432
DB_NAME=game_insights
DB_USER=postgres
DB_PASSWORD=your_password
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the pipeline:

```bash
python src/pipeline.py
```

---

## Logging

Execution logs are written to:

```text
logs/pipeline.log
```

The log file records:

* API extraction events
* Database operations
* Report generation
* Errors and exceptions

---

## Features

* API data extraction with pagination
* Data transformation using Pandas
* PostgreSQL integration
* Bulk inserts using `executemany()`
* Duplicate protection using `ON CONFLICT`
* CSV analytics report generation
* Structured logging
* Environment variable configuration

---

## Future Improvements

* Add unit tests with Pytest
* Generate additional analytics reports
* Refactor into multiple modules

---

## Author

**Aniruddha Shil**
Engineering Student, VIT Bhopal
