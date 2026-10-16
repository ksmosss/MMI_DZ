"""Vercel Python Function entrypoint (all API routes under /api)."""
from fastapi import FastAPI
from backend.app.main import app as taskflow_api

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount('/api', taskflow_api)
