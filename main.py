import asyncio
import json
import os
import collections
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
import subprocess
import re

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import psutil
from dotenv import load_dotenv
import tkinter as tk
from tkinter import filedialog

# Load environment variables
load_dotenv()

CONFIG_FILE = "config.json"
MAX_LOG_LINES = 100

class ScriptConfig(BaseModel):
    id: str
    name: str
    path: str
    args: str = ""
    cwd: str = ""
    port: str = ""
    github_url: str = ""
    auto_start: bool

class ScriptStatus(BaseModel):
    id: str
    name: str
    path: str
    args: str = ""
    cwd: str = ""
    port: str = ""
    github_url: str = ""
    auto_start: bool
    is_running: bool
    pid: Optional[int] = None
    discovered_url: Optional[str] = None
    discovered_port: Optional[str] = None

# Global state
class ProcessState:
    def __init__(self):
        self.process: asyncio.subprocess.Process | None = None
        self.pid: int | None = None
        self.log_buffer: collections.deque = collections.deque(maxlen=MAX_LOG_LINES)
        self.listeners: List[asyncio.Queue] = []
        self.task: asyncio.Task | None = None
        self.discovered_url: Optional[str] = None
        self.discovered_port: Optional[str] = None

processes: Dict[str, ProcessState] = collections.defaultdict(ProcessState)

def load_config() -> List[Dict[str, Any]]:
    if not os.path.exists(CONFIG_FILE):
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_config(config: List[Dict[str, Any]]):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def kill_process_tree(pid: int):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        # Tuer d'abord les enfants
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        # Puis le parent
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        # Attendre que tout le monde meure, sinon forcer
        gone, alive = psutil.wait_procs(children + [parent], timeout=3)
        for p in alive:
            try:
                p.kill()
            except psutil.NoSuchProcess:
                pass
    except psutil.NoSuchProcess:
        pass

def find_zombie_pid(script: dict) -> Optional[int]:
    target_path = script.get("path", "").replace("\\", "/").lower()
    target_cwd = script.get("cwd", "").replace("\\", "/").lower()
    target_args = script.get("args", "").replace("\\", "/").lower()
    
    for p in psutil.process_iter(['pid', 'cmdline', 'cwd']):
        try:
            cmdline = p.info.get('cmdline')
            if not cmdline:
                continue
            cmd_str = " ".join(cmdline).replace("\\", "/").lower()
            
            if target_path in cmd_str:
                if target_args:
                    clean_args = target_args.replace('"', '').replace("'", "")
                    clean_cmd = cmd_str.replace('"', '').replace("'", "")
                    if clean_args not in clean_cmd:
                        continue
                        
                p_cwd = p.info.get('cwd', '')
                if p_cwd:
                    p_cwd = p_cwd.replace("\\", "/").lower()
                if target_cwd and target_cwd != p_cwd:
                    if p_cwd:
                        continue
                return p.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

async def read_stream(stream: asyncio.StreamReader, script_id: str, is_error: bool = False):
    state = processes[script_id]
    while True:
        line_bytes = await stream.readline()
        if not line_bytes:
            break
        line_str = line_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
        
        # Auto-detect URL from logs
        if not state.discovered_url:
            match = re.search(r'(https?://(?:localhost|127\.0\.0\.1|0\.0\.0\.0|[\w\.-]+):(\d+))', line_str)
            if match:
                state.discovered_url = match.group(1)
                # If psutil couldn't find it, fallback to log regex
                if not state.discovered_port:
                    state.discovered_port = match.group(2)
        
        # Smart prefixing: stderr is used for all logs in Python. 
        # Don't flag as ERROR if it explicitly says INFO, DEBUG or WARNING.
        prefix = ""
        if is_error:
            if not re.search(r'(INFO|DEBUG|WARNING)', line_str.upper()):
                prefix = "[ERROR] "

        log_entry = f"{prefix}{line_str}"
        
        state.log_buffer.append(log_entry)
        for queue in state.listeners:
            try:
                queue.put_nowait(log_entry)
            except asyncio.QueueFull:
                pass

async def run_process(script_id: str, script_path: str):
    state = processes[script_id]
    # Reset discovered info
    state.discovered_url = None
    state.discovered_port = None
    
    config = load_config()
    script = next((s for s in config if s["id"] == script_id), None)
    args = script.get("args", "") if script else ""
    cwd = script.get("cwd", "") if script else ""
    
    import shlex
    args_list = shlex.split(args) if args else []
    
    cmd = []
    if script_path.lower().endswith('.py'):
        cmd = ["python", script_path] + args_list
    else:
        cmd = [script_path] + args_list
        
    try:
        # Prevent PyManager's environment variables from leaking to child processes
        env = os.environ.copy()
        env.pop("PORT", None)
        env.pop("HOST", None)
        env.pop("VIRTUAL_ENV", None) # Important: Ne pas forcer les enfants à utiliser le .venv de PyManager
        env["PYTHONUNBUFFERED"] = "1"

        creationflags = 0
        if os.name == 'nt':
            creationflags = subprocess.CREATE_NO_WINDOW
            
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd if cwd else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            creationflags=creationflags,
            env=env
        )
        state.process = process
        state.pid = process.pid
        
        state.log_buffer.append(f"--- Process started (PID: {process.pid}) ---")
        
        stdout_task = asyncio.create_task(read_stream(process.stdout, script_id))
        stderr_task = asyncio.create_task(read_stream(process.stderr, script_id, is_error=True))
        
        await process.wait()
        await stdout_task
        await stderr_task
        
    except Exception as e:
        state.log_buffer.append(f"--- Failed to start: {e} ---")
    finally:
        state.log_buffer.append(f"--- Process exited ---")
        state.process = None
        state.pid = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    for script in config:
        if script.get("auto_start"):
            script_id = script["id"]
            script_path = script["path"]
            if os.path.exists(script_path):
                # Vérifier s'il n'est pas DÉJÀ en train de tourner !
                zombie_pid = find_zombie_pid(script)
                if zombie_pid:
                    # On l'adopte, on ne le redémarre pas pour éviter le crash
                    processes[script_id].pid = zombie_pid
                else:
                    processes[script_id].task = asyncio.create_task(run_process(script_id, script_path))
    yield
    for state in processes.values():
        if state.pid:
            kill_process_tree(state.pid)

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/scripts")
async def get_scripts():
    config = load_config()
    results = []
    for s in config:
        script_id = s["id"]
        state = processes.get(script_id)
        
        is_running = False
        pid = None
        
        if state:
            if state.process and state.process.returncode is None:
                is_running = True
                pid = state.pid
            elif state.pid:
                # We had a zombie PID stored
                is_running = True
                pid = state.pid
                
        # Si on n'a rien, on cherche un zombie
        if not is_running:
            zombie_pid = find_zombie_pid(s)
            if zombie_pid:
                pid = zombie_pid
                is_running = True
                if state:
                    state.pid = pid
        
        detected_port = state.discovered_port if state else None
        
        # Double check with psutil
        if is_running and pid:
            try:
                proc = psutil.Process(pid)
                if not proc.is_running():
                    is_running = False
                    pid = None
                    if state:
                        state.pid = None
                else:
                    # Attempt to find listening ports via psutil
                    ports = []
                    try:
                        for conn in proc.connections(kind='inet'):
                            if conn.status == psutil.CONN_LISTEN:
                                ports.append(str(conn.laddr.port))
                    except Exception:
                        pass
                    if ports:
                        detected_port = ",".join(list(set(ports)))
            except Exception:
                is_running = False
                pid = None
                if state:
                    state.pid = None
                
        results.append(ScriptStatus(
            id=s["id"],
            name=s["name"],
            path=s["path"],
            args=s.get("args", ""),
            cwd=s.get("cwd", ""),
            port=s.get("port", ""),
            github_url=s.get("github_url", ""),
            auto_start=s["auto_start"],
            is_running=is_running,
            pid=pid,
            discovered_url=state.discovered_url if state else None,
            discovered_port=detected_port
        ))
    return results

@app.post("/api/scripts")
async def add_script(script: ScriptConfig):
    config = load_config()
    if any(s["id"] == script.id for s in config):
        raise HTTPException(status_code=400, detail="Script ID already exists")
    config.append(script.dict())
    save_config(config)
    return {"status": "success"}

@app.put("/api/scripts/{script_id}")
async def edit_script(script_id: str, script: ScriptConfig):
    config = load_config()
    for i, s in enumerate(config):
        if s["id"] == script_id:
            # Update values while keeping original ID just in case
            updated_script = script.dict()
            updated_script["id"] = script_id 
            config[i] = updated_script
            save_config(config)
            return {"status": "success"}
    raise HTTPException(status_code=404, detail="Script not found")

@app.delete("/api/scripts/{script_id}")
async def delete_script(script_id: str):
    config = load_config()
    config = [s for s in config if s["id"] != script_id]
    save_config(config)
    
    # Also stop if running
    state = processes.get(script_id)
    if state and state.pid:
        kill_process_tree(state.pid)
        state.pid = None
    return {"status": "success"}

@app.post("/api/scripts/{script_id}/start")
async def start_script(script_id: str):
    config = load_config()
    script = next((s for s in config if s["id"] == script_id), None)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
        
    state = processes[script_id]
    if (state.process and state.process.returncode is None) or state.pid:
        raise HTTPException(status_code=400, detail="Script is already running")
        
    state.task = asyncio.create_task(run_process(script_id, script["path"]))
    return {"status": "success"}

@app.post("/api/scripts/{script_id}/stop")
async def stop_script(script_id: str):
    state = processes.get(script_id)
    if not state or not state.pid:
        raise HTTPException(status_code=400, detail="Script is not running")
        
    try:
        kill_process_tree(state.pid)
        state.pid = None
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import signal

@app.post("/api/shutdown")
async def shutdown_server():
    # Arrêter tous les enfants proprement
    for state in processes.values():
        if state.pid:
            kill_process_tree(state.pid)
    
    # Se suicider (le signal.SIGTERM sur Windows tue le processus)
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting down"}

@app.websocket("/ws/logs/{script_id}")
async def websocket_logs(websocket: WebSocket, script_id: str):
    await websocket.accept()
    state = processes[script_id]
    
    # Send history
    for line in state.log_buffer:
        await websocket.send_text(line)
        
    # Listen for new logs
    queue = asyncio.Queue()
    state.listeners.append(queue)
    
    async def listen_to_client():
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
            
    async def send_logs():
        try:
            while True:
                log_line = await queue.get()
                await websocket.send_text(log_line)
        except WebSocketDisconnect:
            pass
            
    listen_task = asyncio.create_task(listen_to_client())
    send_task = asyncio.create_task(send_logs())
    
    done, pending = await asyncio.wait(
        [listen_task, send_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    
    for task in pending:
        task.cancel()
        
    state.listeners.remove(queue)

import ctypes
import ctypes.wintypes

def open_file_dialog():
    import subprocess
    import os
    
    code = """
import tkinter as tk
from tkinter import filedialog
import sys

root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', 1)
file_path = filedialog.askopenfilename(
    title="Sélectionner le script ou l'exécutable Python",
    filetypes=[("Exécutables et Scripts", "*.exe;*.bat;*.py"), ("Tous les fichiers", "*.*")]
)
root.destroy()

if file_path:
    print(file_path)
else:
    print("")
"""
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        out = subprocess.check_output(["python", "-c", code], text=True, creationflags=creationflags)
        return out.strip()
    except Exception as e:
        print("File dialog error:", e)
        return ""

def open_folder_dialog():
    import subprocess
    import os
    
    code = """
import tkinter as tk
from tkinter import filedialog
import sys

root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', 1)
folder_path = filedialog.askdirectory(title="Sélectionner un dossier")
root.destroy()

if folder_path:
    print(folder_path)
else:
    print("")
"""
    try:
        # Note: CREATE_NO_WINDOW prevents a black cmd box from flashing
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        out = subprocess.check_output(["python", "-c", code], text=True, creationflags=creationflags)
        return out.strip()
    except Exception as e:
        print("Folder dialog error:", e)
        return ""

@app.get("/api/browse_folder")
async def browse_folder():
    folder_path = await run_in_threadpool(open_folder_dialog)
    return {"path": folder_path}

@app.get("/api/browse")
async def browse_file():
    file_path = await run_in_threadpool(open_file_dialog)
    return {"path": file_path}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port)
