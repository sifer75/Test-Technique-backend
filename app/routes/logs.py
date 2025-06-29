from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List
from datetime import datetime
from opensearchpy import OpenSearch
import os
from app.models import LogEntry, LogEntryResponse
from dateutil.relativedelta import relativedelta


router = APIRouter(prefix="/logs", tags=["Logs"])

client = OpenSearch(
    hosts=[{"host": os.getenv("OPENSEARCH_HOST", "localhost"), "port": 9200}],
    http_auth=(os.getenv("OPENSEARCH_USER", "admin"), os.getenv("OPENSEARCH_PASS", "admin")),
    use_ssl=False,
    verify_certs=False
)

@router.post("/", response_model=LogEntryResponse)
def insert_log(log: LogEntry):
    try:
        timestamp = datetime.utcnow()
        index_name = f"logs-{timestamp.strftime('%Y.%m.%d')}"
        doc = {
            **log.dict(),
            "timestamp": timestamp.isoformat()
        }
        response = client.index(index=index_name, body=doc)
        return {
            "id": response["_id"],
            **doc
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
def search_logs(
    q: Optional[str] = Query(None, description="Full-text search in 'message' field"),
    level: Optional[str] = Query(None, description="Filter by log level (e.g. info, warning)"),
    date: Optional[str] = Query(None, description="Filter by year or year + month or all"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    size: int = Query(20, ge=1, le=100, description="Number of logs to return"),
    page: int = Query(1, ge=1, description="Page number for pagination")
):
    try:
        must_clauses = []

        if q:
            must_clauses.append({
                    "bool": {
                        "should": [
                            {
                                "wildcard": {
                                    "message.keyword": f"*{q.lower()}*"
                                }
                            },
                            {
                                "match": {
                                    "message": {
                                        "query": q,
                                        "fuzziness": "AUTO"
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                })
        if level:
            must_clauses.append({"term": {"level.keyword": level}})

        if service:
            must_clauses.append({"term": {"service.keyword": service}})

        if date:
            try:

                if len(date) == 4:
                    start = datetime.strptime(date, "%Y")
                    end = start + relativedelta(years=1)

                elif len(date) == 7:
                    start = datetime.strptime(date, "%Y-%m")
                    end = start + relativedelta(months=1)

                elif len(date) == 10:
                    start = datetime.strptime(date, "%Y-%m-%d")
                    end = start + relativedelta(days=1)

                else:
                    raise ValueError("Invalid date format")

                must_clauses.append({
                    "range": {
                        "timestamp": {
                            "gte": start.isoformat(),
                            "lt": end.isoformat()
                        }
                    }
                })
            except ValueError as e:
              print(f"❌ Invalid date: {date} → {e}")
              raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY, YYYY-MM, or YYYY-MM-DD")

        query_body = {
            "query": {
                "bool": {
                    "must": must_clauses or [{"match_all": {}}]
                }
            },
            "sort": [{"timestamp": {"order": "desc"}}],
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
        import traceback
        print("❌ Internal Server Error")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error. Check logs for details.")


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_logs():
    try:
        response = client.indices.delete(index="logs-*")
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))