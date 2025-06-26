# app/routes/logs.py
from fastapi import APIRouter, HTTPException, Query
from app.models import LogEntry
from datetime import datetime
from opensearchpy import OpenSearch
from typing import Optional
import os

router = APIRouter(prefix="/logs", tags=["Logs"])

# OpenSearch connection (adjust parameters as needed)
client = OpenSearch(
    hosts=[{"host": os.getenv("OPENSEARCH_HOST", "localhost"), "port": 9200}],
    http_auth=(os.getenv("OPENSEARCH_USER", "admin"), os.getenv("OPENSEARCH_PASS", "admin")),
    use_ssl=False,
    verify_certs=False
)

@router.post("/", status_code=201)
def insert_log(log: LogEntry):
    try:
        # Index format: logs-YYYY.MM.DD
        index_name = f"logs-{log.timestamp.strftime('%Y.%m.%d')}"

        # Convert the log entry to a dictionary
        doc = log.dict()

        # Index the document into OpenSearch
        response = client.index(index=index_name, body=doc)

        # Return the indexed log with the generated _id
        return {
            "id": response["_id"],
            **doc
        }

    except Exception as e:
        # Handle unexpected errors during indexing
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
def search_logs(
    q: Optional[str] = Query(None, description="Full-text search in 'message' field"),
    level: Optional[str] = Query(None, description="Filter by log level (e.g. info, warning)"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    size: int = Query(10, ge=1, le=100, description="Number of logs to return"),
    page: int = Query(1, ge=1, description="Page number for pagination")
):
    try:
        must_clauses = []

        if q:
            must_clauses.append({"match": {"message": q}})

        if level:
            must_clauses.append({"term": {"level.keyword": level}})

        if service:
            must_clauses.append({"term": {"service.keyword": service}})

        query_body = {
            "query": {
                "bool": {
                    "must": must_clauses or [{"match_all": {}}]
                }
            },
            "sort": [
                {"timestamp": {"order": "desc"}}
            ],
            "from": (page - 1) * size,
            "size": size
        }

        response = client.search(index="logs-*", body=query_body)

        results = [
            {
                "id": hit["_id"],
                **hit["_source"]
            }
            for hit in response["hits"]["hits"]
        ]

        return {
            "total": response["hits"]["total"]["value"],
            "page": page,
            "size": size,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
