from tempfile import TemporaryDirectory
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import subprocess
import os
import docker
import tempfile
import os
import time

class CodeRunRequest(BaseModel):
    code: str
    language: str

class CodeExecutionRequest(BaseModel):
    code : str
    language : str

#Функция запуска в докере
def run_code_in_docker(code: str, language: str) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Определяем расширение файла и команду
        if language == "python":
            filename = "script.py"
            cmd = f"python3 /workspace/{filename}"
        elif language == "c":
            filename = "program.c"
            cmd = f"gcc /workspace/{filename} -o /workspace/program && /workspace/program"
        elif language == "c++":
            filename = "program.cpp"
            cmd = f"g++ /workspace/{filename} -o /workspace/program && /workspace/program"
        else:
            return {"error": "Unsupported language"}

        filepath = os.path.join(tmpdir, filename)
        with open(filepath, "w") as f:
            f.write(code)

        # Получаем текущий UID и GID пользователя
        uid = os.getuid()
        gid = os.getgid()

        try:
            container = docker_client.containers.run(
                image="code-runner",
                command=["/bin/sh", "-c", cmd],
                working_dir="/workspace",
                volumes={tmpdir: {"bind": "/workspace", "mode": "rw", "selinux" : 'z'}},
                stdout=True,
                stderr=True,
                detach=True,
                mem_limit="128m",
                nano_cpus=int(1e9),
                network_disabled=True,
                user=f"{uid}:{gid}",  # запускаем от нашего UID
                remove=True,  # добавим remove=True, чтобы контейнер удалился после завершения
            )
            # Ждём завершения с таймаутом (но теперь не нужно удалять вручную, т.к. remove=True)
            result = container.wait(timeout=10)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            # container уже удалён из-за remove=True
            return {
                "output": logs,
                "error": "",
                "time": 0
            }
        except docker.errors.ContainerError as e:
            return {"error": f"Container error: {e.stderr.decode('utf-8') if e.stderr else 'Unknown'}"}
        except docker.errors.APIError as e:
            return {"error": f"Docker API error: {str(e)}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}

def run_code(code: str, language: str) -> str:
    with TemporaryDirectory() as tmpdir:
        if language == "python":
            filepath = os.path.join(tmpdir, "code.py")
            with open(filepath, "w") as f:
                f.write(code)
            result = subprocess.run(
                ["python3", filepath],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout + result.stderr
            return output if output else "Успешно"

        elif language == "c":
            source = os.path.join(tmpdir, "code.c")
            executable = os.path.join(tmpdir, "code")
            with open(source, "w") as f:
                f.write(code)

            compile_result = subprocess.run(
                ["gcc", source, "-o", executable],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                return f"Ошибка компиляции: \n{compile_result.stderr}"
            run_result = subprocess.run(
                [executable],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = run_result.stdout + run_result.stderr
            return output if output else "Успешно"

        elif language == "cpp":
            source = os.path.join(tmpdir, "code.cpp")
            executable = os.path.join(tmpdir, "code")
            with open(source, "w") as f:
                f.write(code)

            compile_result = subprocess.run(
                ["g++", source, "-o", executable],
                capture_output=True,
                text=True
            )
            if compile_result.returncode != 0:
                return f"Ошибка компиляции: \n{compile_result.stderr}"
            run_result = subprocess.run(
                [executable],
                capture_output=True,
                texgitt=True,
                timeout=5
            )
            output = run_result.stdout + run_result.stderr
            return output if output else "Успешно"

        else:
            raise ValueError(f"Неподдерживаемый язык: {language}")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

docker_client = docker.from_env()

templates = Jinja2Templates(directory="templates")

@app.post("/run_docker")
async def execute_docker(request: CodeExecutionRequest):
    result = run_code_in_docker(request.code, request.language)
    return result

@app.post("/run")
async def run_code_endpoint(request: CodeRunRequest):
    try:
        output = run_code(request.code, request.language)
        return {"output": output}
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail="Превышено время выполнения (5 секунд)")
    except Exception as e:
        # Возвращаем 400 с текстом ошибки для отладки
        raise HTTPException(status_code=400, detail=str(e))
    

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("editor.html",{"request": request})