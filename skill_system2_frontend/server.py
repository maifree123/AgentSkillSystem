"""
Minimal FastAPI frontend for skill_system2.
"""
from __future__ import annotations

import os
import sys
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(override=True)

from skill_system2 import create_skill_agent, SkillSystemConfig

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"
UPLOAD_DIR = PROJECT_ROOT / "skill_system2" / "uploads"


class InitPayload(BaseModel):
    model: str = "gpt-4o-mini"


class MessagePayload(BaseModel):
    message: str


class AgentManager:
    def __init__(self):
        self.agent = None
        self.skills_info: Dict[str, Any] = {}
        self.loader_tool_map: Dict[str, str] = {}
        self.skills_loaded: List[str] = []
        self.history: List[Dict[str, str]] = []

    def is_ready(self) -> bool:
        return self.agent is not None


manager = AgentManager()


def load_skills_info() -> Dict[str, Any]:
    skills_info: Dict[str, Any] = {}
    skills_dir = PROJECT_ROOT / "skill_system2" / "skills"
    if not skills_dir.exists():
        return skills_info

    for skill_folder in skills_dir.iterdir():
        if not skill_folder.is_dir() or skill_folder.name.startswith("_"):
            continue

        skill_py = skill_folder / "skill.py"
        instructions_md = skill_folder / "instructions.md"
        if not skill_py.exists():
            continue

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"skill_{skill_folder.name}",
                skill_py
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "create_skill"):
                skill_instance = module.create_skill(skill_folder)
                metadata = skill_instance.metadata
                tools = skill_instance.get_tools()
                tool_list = []
                for tool in tools:
                    tool_list.append({
                        "name": tool.name,
                        "description": tool.description or ""
                    })

                loader_tool = skill_instance.get_loader_tool()
                loader_tool_info = {
                    "name": loader_tool.name,
                    "description": loader_tool.description or "",
                }

                instructions = ""
                if instructions_md.exists():
                    instructions = instructions_md.read_text(encoding="utf-8")

                skills_info[metadata.name] = {
                    "name": metadata.name,
                    "description": metadata.description,
                    "instructions": instructions,
                    "tools": tool_list,
                    "loader_tool": loader_tool_info,
                    "version": metadata.version,
                    "tags": metadata.tags,
                    "author": metadata.author,
                }
        except Exception as e:
            logger.warning(f"Failed to load skill {skill_folder.name}: {e}")

    return skills_info


# 保存上传文件到指定目录
def save_upload_file(upload: UploadFile, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "upload.bin").name
    unique_name = f"{Path(safe_name).stem}_{uuid.uuid4().hex}{Path(safe_name).suffix}"
    target_path = target_dir / unique_name

    with target_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)

    return target_path


# 读取上传文件的基础元信息
def build_file_metadata(file_path: Path, content_type: Optional[str]) -> Dict[str, Any]:
    return {
        "name": file_path.name,
        "path": str(file_path),
        "size": file_path.stat().st_size,
        "content_type": content_type,
        "extension": file_path.suffix.lower(),
    }


def extract_history(result_messages: List[Any]) -> List[Dict[str, str]]:
    history: List[Dict[str, str]] = []
    for msg in result_messages:
        msg_type = msg.__class__.__name__
        if msg_type == "HumanMessage" and msg.content:
            history.append({"role": "user", "content": msg.content})
        elif msg_type == "AIMessage" and msg.content:
            history.append({"role": "assistant", "content": msg.content})
    return history


def merge_loaded_skills(current: List[str], new_items: List[str]) -> List[str]:
    seen = set(current)
    merged = list(current)
    for item in new_items:
        if item not in seen:
            merged.append(item)
            seen.add(item)
    return merged


def parse_agent_result(result: Dict[str, Any]) -> Dict[str, Any]:
    ai_response = ""
    tool_calls = []
    skills_loaded = result.get("skills_loaded", [])

    for msg in result.get("messages", []):
        msg_type = msg.__class__.__name__
        if msg_type == "AIMessage" and msg.content:
            ai_response = msg.content

        if msg_type == "AIMessage" and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "name": tc.get("name") if isinstance(tc, dict) else tc.name,
                    "args": tc.get("args") if isinstance(tc, dict) else tc.args,
                })

        if msg_type == "ToolMessage":
            tool_calls.append({
                "name": msg.name if hasattr(msg, "name") else "unknown",
                "result": msg.content,
            })

    return {
        "response": ai_response,
        "skills_loaded": skills_loaded,
        "tool_calls": tool_calls,
    }


app = FastAPI(title="Skill System 2 Frontend")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/init")
def init_agent(payload: InitPayload):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return JSONResponse(
            status_code=400,
            content={"error": "Missing OPENAI_API_KEY in .env or environment"},
        )

    base_url = os.getenv("OPENAI_BASE_URL")
    model_instance = ChatOpenAI(
        api_key=api_key,
        model=payload.model,
        temperature=0.7,
        base_url=base_url,
    )

    config = SkillSystemConfig(
        skills_dir=PROJECT_ROOT / "skill_system2" / "skills",
        state_mode="replace",
        verbose=False,
        middleware_enabled=True,
    )

    manager.agent = create_skill_agent(model=model_instance, config=config)
    manager.skills_info = load_skills_info()
    manager.loader_tool_map = {
        info["loader_tool"]["name"]: skill_name
        for skill_name, info in manager.skills_info.items()
        if info.get("loader_tool")
    }
    manager.skills_loaded = []
    manager.history = []
    skills = manager.agent.list_skills()

    return {
        "ok": True,
        "skills": skills,
        "skills_info": manager.skills_info,
        "model": payload.model,
    }


@app.post("/message")
def send_message(payload: MessagePayload):
    if not manager.is_ready():
        return JSONResponse(
            status_code=400,
            content={"error": "Agent not initialized"},
        )

    result = manager.agent.invoke({
        "messages": manager.history + [{"role": "user", "content": payload.message}],
        "skills_loaded": manager.skills_loaded,
    })
    parsed = parse_agent_result(result)

    # Update skill load state based on loader tool usage.
    newly_loaded = []
    for tool_call in parsed.get("tool_calls", []):
        tool_name = tool_call.get("name")
        if tool_name in manager.loader_tool_map:
            newly_loaded.append(manager.loader_tool_map[tool_name])
    manager.skills_loaded = merge_loaded_skills(
        manager.skills_loaded,
        result.get("skills_loaded", []) + newly_loaded
    )

    # Refresh history from result if available.
    result_messages = result.get("messages", [])
    if result_messages:
        manager.history = extract_history(result_messages)
    else:
        if payload.message:
            manager.history.append({"role": "user", "content": payload.message})
        if parsed.get("response"):
            manager.history.append({"role": "assistant", "content": parsed["response"]})

    parsed["skills_loaded"] = manager.skills_loaded
    return parsed


# 上传 PDF/CSV 等文件并返回路径信息
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in [".pdf", ".csv"]:
        raise HTTPException(status_code=400, detail="Only PDF or CSV files are supported")

    saved_path = save_upload_file(file, UPLOAD_DIR)
    return {
        "ok": True,
        "file": build_file_metadata(saved_path, file.content_type),
        "message": "Upload success",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=10021,
        reload=False,
        log_level="warning",
    )
