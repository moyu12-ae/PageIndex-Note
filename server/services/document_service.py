import os
import sys
import json
import time
import hashlib
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict

RESULTS_DIR = Path(__file__).parent.parent.parent / "results"
UPLOADS_DIR = Path(__file__).parent.parent.parent / "uploads"
METADATA_FILE = RESULTS_DIR / "_metadata.json"

# Ensure dirs exist
RESULTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)


# ========== Progress Tracking ==========

@dataclass
class TaskProgress:
    status: str = "pending"
    stage: str = ""
    percent: int = 0
    message: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    waiters: list = field(default_factory=list)


class ProgressTracker:
    def __init__(self):
        self._tasks: Dict[str, TaskProgress] = {}

    def create(self, task_id: str):
        self._tasks[task_id] = TaskProgress()

    def get(self, task_id: str) -> Optional[TaskProgress]:
        return self._tasks.get(task_id)

    def update(self, task_id: str, stage: str, percent: int, message: str = ""):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.stage = stage
        task.percent = percent
        task.message = message
        task.status = "processing"
        for event in task.waiters:
            event.set()

    def complete(self, task_id: str, result: dict = None):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "completed"
        task.percent = 100
        task.result = result
        for event in task.waiters:
            event.set()

    def fail(self, task_id: str, error: str):
        task = self._tasks.get(task_id)
        if not task:
            return
        task.status = "failed"
        task.error = error
        for event in task.waiters:
            event.set()

    async def subscribe(self, task_id: str):
        """Async generator yielding progress updates."""
        task = self._tasks.get(task_id)
        if not task:
            return

        last_percent = -1
        while task.status not in ("completed", "failed"):
            if task.percent != last_percent:
                last_percent = task.percent
                yield {
                    "stage": task.stage,
                    "percent": task.percent,
                    "message": task.message
                }
            event = asyncio.Event()
            task.waiters.append(event)
            try:
                await asyncio.wait_for(event.wait(), timeout=30)
            except asyncio.TimeoutError:
                # Send heartbeat
                yield {"stage": task.stage, "percent": task.percent, "message": "Still processing..."}
            finally:
                if event in task.waiters:
                    task.waiters.remove(event)

        # Yield final state
        if task.status == "completed":
            yield {"status": "completed", "percent": 100}
        else:
            yield {"status": "failed", "message": task.error}


progress_tracker = ProgressTracker()


# ========== Metadata Storage ==========

def generate_document_id(filename: str) -> str:
    raw = f"{filename}-{time.time()}"
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def load_all_metadata() -> dict:
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_metadata(doc_id: str, meta: dict):
    all_meta = load_all_metadata()
    all_meta[doc_id] = meta
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)


def delete_metadata(doc_id: str):
    all_meta = load_all_metadata()
    all_meta.pop(doc_id, None)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(all_meta, f, ensure_ascii=False, indent=2)


# ========== PDF Processing (subprocess) ==========

async def process_pdf(file_path: str, opt_dict: dict) -> dict:
    """Run page_index_main in a separate subprocess via python -c."""
    import subprocess
    import tempfile

    # Write opt_dict to a temp file
    opt_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    json.dump(opt_dict, opt_file, ensure_ascii=False)
    opt_file.close()

    result_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
    result_file.close()

    script = f'''
import sys, json
sys.path.insert(0, r"{Path(__file__).parent.parent.parent}")
from types import SimpleNamespace
from pageindex.page_index import page_index_main

with open(r"{opt_file.name}", "r", encoding="utf-8") as f:
    opt_dict = json.load(f)
opt = SimpleNamespace(**opt_dict)
result = page_index_main(r"{file_path}", opt)
with open(r"{result_file.name}", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("DONE")
'''

    loop = asyncio.get_running_loop()
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-c', script,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    # Clean up opt file
    try:
        os.unlink(opt_file.name)
    except Exception:
        pass

    if proc.returncode != 0:
        error_msg = stderr.decode('utf-8', errors='replace').strip()
        try:
            os.unlink(result_file.name)
        except Exception:
            pass
        raise RuntimeError(f"PDF processing failed:\n{error_msg}")

    # Read result
    with open(result_file.name, "r", encoding="utf-8") as f:
        result = json.load(f)
    try:
        os.unlink(result_file.name)
    except Exception:
        pass

    return result


async def process_markdown(file_path: str, params: dict) -> dict:
    """md_to_tree is async and cooperates with our event loop."""
    from pageindex.page_index_md import md_to_tree
    result = await md_to_tree(
        md_path=file_path,
        if_thinning=params.get("if_thinning", False),
        min_token_threshold=params.get("min_token_threshold", 5000),
        if_add_node_summary=params.get("if_add_node_summary", "yes"),
        summary_token_threshold=params.get("summary_token_threshold", 200),
        model=params.get("model", "deepseek-chat"),
        if_add_doc_description=params.get("if_add_doc_description", "no"),
        if_add_node_text=params.get("if_add_node_text", "no"),
        if_add_node_id=params.get("if_add_node_id", "yes"),
    )
    return result


# ========== Orchestration ==========

def _get_config_values():
    """Read current config from .env and config.yaml."""
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    import yaml
    config_path = Path(__file__).parent.parent.parent / "pageindex" / "config.yaml"
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg


async def orchestrate_processing(document_id: str, file_path: str, file_type: str):
    """Wraps the actual processing with estimated progress stages."""
    tracker = progress_tracker
    cfg = _get_config_values()

    tracker.update(document_id, "uploading", 5, "File received, starting processing...")
    await asyncio.sleep(0.5)

    try:
        if file_type == "pdf":
            tracker.update(document_id, "extracting_text", 15, "Extracting text from PDF...")
            await asyncio.sleep(0.3)
            tracker.update(document_id, "analyzing_structure", 30, "Analyzing document structure with LLM...")

            opt_dict = {
                "model": cfg.get("model", "deepseek-chat"),
                "toc_check_page_num": cfg.get("toc_check_page_num", 20),
                "max_page_num_each_node": cfg.get("max_page_num_each_node", 10),
                "max_token_num_each_node": cfg.get("max_token_num_each_node", 20000),
                "if_add_node_id": cfg.get("if_add_node_id", "yes"),
                "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
                "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
                "if_add_node_text": cfg.get("if_add_node_text", "no"),
            }

            result = await process_pdf(file_path, opt_dict)

        elif file_type == "markdown":
            tracker.update(document_id, "parsing_markdown", 15, "Parsing Markdown structure...")
            await asyncio.sleep(0.3)
            tracker.update(document_id, "building_tree", 30, "Building tree with LLM analysis...")

            params = {
                "model": cfg.get("model", "deepseek-chat"),
                "if_thinning": cfg.get("if_thinning", False),
                "min_token_threshold": cfg.get("min_token_threshold", 5000),
                "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
                "summary_token_threshold": cfg.get("summary_token_threshold", 200),
                "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
                "if_add_node_text": cfg.get("if_add_node_text", "no"),
                "if_add_node_id": cfg.get("if_add_node_id", "yes"),
            }

            result = await process_markdown(file_path, params)

        else:
            # txt, json, csv, word → convert to Markdown first, then process
            from server.services.converter_service import convert_to_markdown

            type_labels = {
                "text": "TXT",
                "json": "JSON",
                "csv": "CSV",
                "word": "Word",
            }
            label = type_labels.get(file_type, file_type.upper())

            tracker.update(document_id, "converting", 10,
                           f"Converting {label} to Markdown...")
            await asyncio.sleep(0.3)

            # Convert to markdown
            md_path = str(UPLOADS_DIR / f"{document_id}_converted.md")
            convert_to_markdown(file_path, md_path, file_type)

            tracker.update(document_id, "parsing_markdown", 25,
                           f"Parsing converted Markdown structure...")
            await asyncio.sleep(0.3)
            tracker.update(document_id, "building_tree", 40,
                           "Building tree with LLM analysis...")

            params = {
                "model": cfg.get("model", "deepseek-chat"),
                "if_thinning": cfg.get("if_thinning", False),
                "min_token_threshold": cfg.get("min_token_threshold", 5000),
                "if_add_node_summary": cfg.get("if_add_node_summary", "yes"),
                "summary_token_threshold": cfg.get("summary_token_threshold", 200),
                "if_add_doc_description": cfg.get("if_add_doc_description", "no"),
                "if_add_node_text": cfg.get("if_add_node_text", "no"),
                "if_add_node_id": cfg.get("if_add_node_id", "yes"),
            }

            result = await process_markdown(md_path, params)

            # Clean up converted file
            try:
                os.unlink(md_path)
            except Exception:
                pass

        tracker.update(document_id, "saving", 90, "Saving results...")
        await asyncio.sleep(0.2)

        # Save result
        output_path = RESULTS_DIR / f"{document_id}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        # Update metadata
        meta = load_all_metadata().get(document_id, {})
        meta["status"] = "completed"
        save_metadata(document_id, meta)

        tracker.complete(document_id, result)

    except Exception as e:
        meta = load_all_metadata().get(document_id, {})
        meta["status"] = "failed"
        meta["error"] = str(e)
        save_metadata(document_id, meta)
        tracker.fail(document_id, str(e))
