# DE-Civic-Issues-pipeline-and-Dashboard


This project implements an end-to-end **data pipeline** that ingests 311 civic issue data from the **SeeClickFix API**, loads it into **Elasticsearch**, and visualizes it in **Kibana** with a real-time dashboard.

The pipeline is orchestrated in **Apache NiFi** with custom **Python (Jython) ExecuteScript** processors for API calls, pagination, geospatial transformation, and historical backfill.


---

## Features

- **Automated 311 data ingestion from SeeClickFix API**
  - Fetches issues for a given `place_url` (e.g., `bernalillo-county`) with `per_page=100`.
  - Uses metadata from the API response to loop through **all pages** and load the full dataset.
- **Pagination & backfill**
  - Handles multiple pages via a looping `GetEveryPage` processor.
  - Separate backfill flow to pull **archived** issues (`status=Archived`) and populate historical data.
- **Geospatial processing**
  - Computes a `coords` field as `"lat,lng"` that is mapped as a `geo_point` in Elasticsearch.
  - Enables map-based visualization in Kibana.
- **Idempotent upsert writes**
  - Uses document `id` from SeeClickFix as the Elasticsearch `_id`.
  - Index operation set to **upsert**, preventing duplicate documents when the pipeline re-runs.
- **Real-time dashboard**
  - Kibana dashboard with:
    - Time-series bar chart (issues over time).
    - Metric card (total issue count under current filters).
    - Pie chart (top issue types).
    - Interactive map (issue locations).
    - Markdown panel (context and instructions).
- **Scheduling**
  - NiFi `GenerateFlowFile` triggers the pipeline every **8 hours** (configurable) to pull new data.
- **Extensible & configurable**
  - Place URL, scheduling interval, and indices are configurable via NiFi properties and environment variables.

---

## Tech Stack

- **Data Flow / Orchestration:** Apache NiFi
- **Scripting:** Python (Jython in NiFi `ExecuteScript`)
- **Storage & Analytics:** Elasticsearch
- **Visualization:** Kibana
- **Source API:** SeeClickFix API (311 civic issues)
- **Data Format:** JSON (including geospatial coordinates)

---

## Architecture

High-level architecture:

1. **SeeClickFix API**
   - Provides public JSON API endpoint for civic issues (e.g., `https://seeclickfix.com/api/v2/issues`).

2. **NiFi Data Pipeline**
   - **Trigger:** `GenerateFlowFile` – creates an empty flowfile on schedule to start the flow.
   - **QuerySCF (ExecuteScript):**
     - Calls SeeClickFix API with parameters:
       - `place_url`
       - `per_page=100`
     - Writes the raw JSON response (metadata + issues array) to the flowfile.
   - **SplitJson:**
     - Splits `$.issues` into **one flowfile per issue**.
   - **AddCoords (ExecuteScript):**
     - Reads a single-issue JSON.
     - Adds:
       - `coords = f"{lat},{lng}"`
       - `opendate = created_at.split('T')[0]`
   - **EvaluateJsonPath:**
     - Extracts `id` into a flowfile attribute (used as Elasticsearch `_id`).
   - **PutElasticsearchHttp:**
     - Writes each issue into an Elasticsearch index (e.g., `scf`).
     - Uses:
       - Identifier Attribute = `id`
       - Index Operation = `upsert`.

3. **Pagination & Backfill**
   - **GetEveryPage (ExecuteScript):**
     - Reads the JSON metadata (`metadata.pagination.page`, `metadata.pagination.pages`, `metadata.pagination.next_page_url`).
     - If current page ≤ total pages:
       - Calls `next_page_url` to fetch the next page.
       - Emits new JSON to be split and processed.
       - Success relationship loops back into itself to keep fetching pages.
   - **QuerySCFArchive (ExecuteScript):**
     - Same as `QuerySCF` but adds `status=Archived`.
     - Used to backfill the index with historical issues.
     - Runs once; can be disabled after backfill completes.

4. **Elasticsearch & Kibana**
   - Elasticsearch index `scf` stores issues, with:
     - `coords` mapped as `geo_point`.
   - Kibana uses an index pattern `scf*` with time field `created_at`.
   - Dashboard visualizes counts, categories, and geospatial distribution of issues.

See `docs/architecture-diagram.png` and `docs/nifi-pipeline.png` for diagrams and NiFi canvas screenshots.

---

## Repository Structure
