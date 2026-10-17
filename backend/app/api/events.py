"""UNWIRED. The live flow never calls this module. See REPO-FINDINGS.md item 2.

Server-Sent Events stream for live dashboard updates.
"""
import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/events", tags=["events"])

# TODO: replace with a proper pub/sub (asyncio.Queue per subscriber) fed by simulator/jobs.


@router.get("/stream")
async def stream() -> StreamingResponse:
    async def gen():
        while True:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(gen(), media_type="text/event-stream")
