"""
FastAPI backend for the personal portfolio.

Run:  uvicorn api.main:app --reload --port 8000

All content is loaded from data.json so you can edit it without touching code.
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DATA_PATH = Path(__file__).parent / "data.json"

app = FastAPI(title="Zachary West Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


class Project(BaseModel):
    title: str
    description: str
    tech_stack: list[str]
    github_link: str


class Experience(BaseModel):
    title: str
    company: str
    date_range: str
    description: list[str]
    tech_stack: list[str]


def _load():
    with open(DATA_PATH) as f:
        return json.load(f)


@app.get("/projects", response_model=list[Project])
def get_projects():
    return [Project(**p) for p in _load()["projects"]]


@app.get("/experiences", response_model=list[Experience])
def get_experiences():
    return [Experience(**e) for e in _load()["experiences"]]
