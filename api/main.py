"""
FastAPI backend for the personal portfolio.

Run:  uvicorn api.main:app --reload --port 8000

All content is loaded from data.json. The admin dashboard at /admin
is password-protected via the ADMIN_PASSWORD env var in .env.
Resume uploads are saved directly into the frontend root directory.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv(Path(__file__).parent / ".env")

DATA_PATH = Path(__file__).parent / "data.json"
ADMIN_HTML = Path(__file__).parent / "admin.html"
FRONTEND_ROOT = Path(__file__).parent.parent

app = FastAPI(title="Zachary West Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ────────────────────────────────────────────────────────

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


class PasswordPayload(BaseModel):
    password: str


# ── Data helpers ──────────────────────────────────────────────────

def _load() -> dict:
    with open(DATA_PATH) as f:
        return json.load(f)


def _save(data: dict):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Auth dependency ───────────────────────────────────────────────

def _require_admin(x_admin_password: Optional[str] = Header(None)):
    expected = os.getenv("ADMIN_PASSWORD", "")
    if not expected:
        raise HTTPException(500, "ADMIN_PASSWORD not configured")
    if x_admin_password != expected:
        raise HTTPException(403, "Invalid admin password")


# ── Public read endpoints ─────────────────────────────────────────

@app.get("/projects", response_model=list[Project])
def get_projects():
    return [Project(**p) for p in _load()["projects"]]


@app.get("/experiences", response_model=list[Experience])
def get_experiences():
    return [Experience(**e) for e in _load()["experiences"]]


# ── Password verification (terminal "admin" command) ──────────────

@app.post("/verify-password")
def verify_password(payload: PasswordPayload):
    expected = os.getenv("ADMIN_PASSWORD", "")
    if payload.password != expected:
        raise HTTPException(403, "Invalid password")
    return {"ok": True}


# ── Admin page ────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return ADMIN_HTML.read_text()


@app.post("/admin/verify")
def admin_verify(payload: PasswordPayload):
    expected = os.getenv("ADMIN_PASSWORD", "")
    if payload.password != expected:
        raise HTTPException(403, "Invalid password")
    return {"ok": True}


# ── Admin: Resume Upload ──────────────────────────────────────────

@app.post("/admin/upload-resume", dependencies=[Depends(_require_admin)])
async def upload_resume(file: UploadFile = File(...)):
    dest = FRONTEND_ROOT / "Zachary_West_Resume.pdf"
    with open(dest, "wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return {"ok": True, "filename": "Zachary_West_Resume.pdf", "path": str(dest)}


# ── Admin CRUD: Projects ──────────────────────────────────────────

@app.post("/admin/projects", dependencies=[Depends(_require_admin)])
def create_project(project: Project):
    data = _load()
    data["projects"].append(project.model_dump())
    _save(data)
    return {"ok": True, "count": len(data["projects"])}


@app.put("/admin/projects/{index}", dependencies=[Depends(_require_admin)])
def update_project(index: int, project: Project):
    data = _load()
    if index < 0 or index >= len(data["projects"]):
        raise HTTPException(404, "Project not found")
    data["projects"][index] = project.model_dump()
    _save(data)
    return {"ok": True}


@app.delete("/admin/projects/{index}", dependencies=[Depends(_require_admin)])
def delete_project(index: int):
    data = _load()
    if index < 0 or index >= len(data["projects"]):
        raise HTTPException(404, "Project not found")
    removed = data["projects"].pop(index)
    _save(data)
    return {"ok": True, "removed": removed["title"]}


# ── Admin CRUD: Experiences ───────────────────────────────────────

@app.post("/admin/experiences", dependencies=[Depends(_require_admin)])
def create_experience(exp: Experience):
    data = _load()
    data["experiences"].append(exp.model_dump())
    _save(data)
    return {"ok": True, "count": len(data["experiences"])}


@app.put("/admin/experiences/{index}", dependencies=[Depends(_require_admin)])
def update_experience(index: int, exp: Experience):
    data = _load()
    if index < 0 or index >= len(data["experiences"]):
        raise HTTPException(404, "Experience not found")
    data["experiences"][index] = exp.model_dump()
    _save(data)
    return {"ok": True}


@app.delete("/admin/experiences/{index}", dependencies=[Depends(_require_admin)])
def delete_experience(index: int):
    data = _load()
    if index < 0 or index >= len(data["experiences"]):
        raise HTTPException(404, "Experience not found")
    removed = data["experiences"].pop(index)
    _save(data)
    return {"ok": True, "removed": removed["title"]}
