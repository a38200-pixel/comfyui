# 설치 · 배포 가이드

이 문서는 다음 순서로 진행합니다.

1. [ComfyUI 설치와 모델 다운로드](#1-comfyui-설치와-모델-다운로드) (이미지를 생성하는 GPU PC)
2. [Flask 앱 실행: Docker](#2-flask-앱-실행-docker) (개발 PC)
3. [VM 서버에 배포하기](#3-vm-서버에-배포하기) (UI 수정 → scp 업데이트 → 실행 → 웹 확인)
4. [문제 해결](#4-문제-해결)

## 내 환경 값 정리

아래 표의 값은 사람마다 다릅니다. 문서의 `<...>` 부분을 **본인 값으로 바꿔서** 명령어를 실행하세요.

| 항목 | 표기 | 예시 | 확인 방법 |
| --- | --- | --- | --- |
| ComfyUI를 실행하는 PC의 IP | `<PC_IP>` | `192.168.0.10` | Windows cmd에서 `ipconfig` → IPv4 주소 |
| VM 서버 IP | `<VM_IP>` | `192.168.0.20` | 서버 계정 조회 페이지 |
| VM 계정 ID | `<VM_USER>` | `user` | 서버 계정 조회 페이지 |

> VM 비밀번호는 문서나 코드에 적지 않습니다.

---

## 1. ComfyUI 설치와 모델 다운로드

이 앱은 이미지를 직접 생성하지 않고, **ComfyUI 서버에 워크플로를 보내서** 결과를 받아옵니다.
그래서 NVIDIA GPU가 있는 PC에 ComfyUI를 먼저 설치하고 실행해야 합니다.

### 테스트한 환경

아래 버전에서 동작을 확인했습니다. 다른 버전에서도 대부분 동작하지만, ComfyUI API가 바뀌어 문제가 생기면 이 버전을 기준으로 비교하세요.

| 항목 | 버전 |
| --- | --- |
| ComfyUI | 0.45.0 |
| ComfyUI Frontend | 1.59.1 |
| PyTorch | 2.15.0 + CUDA 13.2 (`cu132`) |
| Python (ComfyUI) | 3.13 |
| GPU | NVIDIA GeForce RTX 3080 (10GB) |
| 모델 | `sd_xl_turbo_1.0_fp16.safetensors` |

> 실행 중인 ComfyUI의 버전은 브라우저에서 `http://<PC_IP>:8188/system_stats`를 열면 `comfyui_version` 항목으로 확인할 수 있습니다.

### 1-1. ComfyUI 설치

**방법 A: Windows 포터블 버전 (가장 쉬움)**

1. [ComfyUI GitHub Releases](https://github.com/comfyanonymous/ComfyUI/releases)에서 `ComfyUI_windows_portable_nvidia.7z`를 받습니다.
2. 7-Zip으로 원하는 위치에 압축을 풉니다. 예: `D:\ComfyUI_windows_portable`
3. 이 앱(또는 다른 PC, VM, Docker 컨테이너)에서 접속할 수 있도록 **외부 접속 허용 옵션**을 켭니다.
   `run_nvidia_gpu.bat`을 메모장으로 열고 마지막 줄 끝에 `--listen 0.0.0.0`을 추가합니다.
   ```bat
   .\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --listen 0.0.0.0
   ```
4. `run_nvidia_gpu.bat`을 더블클릭해 실행합니다.

**방법 B: 직접 설치 (Linux / 수동 설치)**

```bash
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
# PyTorch는 본인 CUDA 버전에 맞게 설치 (https://pytorch.org/get-started/locally/ 참고)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python main.py --listen 0.0.0.0 --port 8188
```

### 1-2. 모델 다운로드 (SDXL Turbo)

이 프로젝트의 워크플로(`static/test.json`)는 **`sd_xl_turbo_1.0_fp16.safetensors`** 체크포인트를 사용합니다.

1. Hugging Face의 [stabilityai/sdxl-turbo](https://huggingface.co/stabilityai/sdxl-turbo/tree/main) 페이지에서 `sd_xl_turbo_1.0_fp16.safetensors`(약 6.9GB)를 받습니다.
   라이선스 동의나 로그인이 필요하면 페이지 안내를 따르세요.
2. 받은 파일을 ComfyUI의 체크포인트 폴더에 넣습니다.
   ```
   ComfyUI/models/checkpoints/sd_xl_turbo_1.0_fp16.safetensors
   ```
   포터블 버전은 `ComfyUI_windows_portable\ComfyUI\models\checkpoints\`입니다.
3. ComfyUI가 실행 중이었다면 재시작합니다.

> 다른 모델을 쓰려면 `static/test.json`의 노드 `"20"`(`CheckpointLoaderSimple`)의 `ckpt_name`을 해당 파일 이름으로 바꿉니다.

### 1-3. 실행 확인

- ComfyUI PC의 브라우저에서 `http://127.0.0.1:8188`이 열리는지 확인합니다.
- 다른 PC나 VM에서 `http://<PC_IP>:8188`이 열리는지 확인합니다. 안 열리면 **Windows 방화벽에서 8188 포트 인바운드를 허용**하세요.
  (Windows 보안 → 방화벽 및 네트워크 보호 → 고급 설정 → 인바운드 규칙 → 새 규칙 → 포트 → TCP 8188)

### 1-4. 워크플로를 바꾸고 싶을 때

ComfyUI 화면에서 워크플로를 만든 뒤 **API 형식으로 저장**해 `static/test.json`을 교체합니다.
(설정에서 Dev mode를 켜면 `Save (API Format)` 메뉴가 보입니다. 최신 버전은 `Workflow > Export (API)`)

교체한 뒤에는 `app2.py`의 노드 번호를 새 워크플로에 맞게 확인하세요.

| 코드 위치 | 기본 노드 ID | 역할 |
| --- | --- | --- |
| `update_prompts(pos_node_id=...)` | `"6"` | Positive 프롬프트 (`CLIPTextEncode`) |
| `update_prompts(neg_node_id=...)` | `"7"` | Negative 프롬프트 (`CLIPTextEncode`) |
| `graph["13"]["inputs"]["noise_seed"]` | `"13"` | 시드 랜덤화 (`SamplerCustom`) |

---

## 2. Flask 앱 실행: Docker

### 2-1. 주소 설정

`docker-compose.yml`의 `environment`를 본인 환경에 맞게 수정합니다.

```yaml
environment:
  COMFY_URL: "http://host.docker.internal:8188"   # 컨테이너 → ComfyUI
  PUBLIC_COMFY_URL: "http://127.0.0.1:8188"       # 브라우저 → 결과 이미지
```

| 상황 | `COMFY_URL` | `PUBLIC_COMFY_URL` |
| --- | --- | --- |
| ComfyUI와 Docker가 같은 PC, 같은 PC 브라우저로 접속 | `http://host.docker.internal:8188` | `http://127.0.0.1:8188` |
| ComfyUI가 다른 PC에 있음 | `http://<PC_IP>:8188` | `http://<PC_IP>:8188` |

`COMFY_URL`은 **Flask 서버(컨테이너)** 가 접속하는 주소이고, `PUBLIC_COMFY_URL`은 **브라우저** 가 결과 이미지를 불러오는 주소입니다.
`host.docker.internal`은 컨테이너 안에서만 통하는 주소라서 `PUBLIC_COMFY_URL`에는 쓸 수 없습니다.

### 2-2. 실행

```bash
docker compose up --build
```

브라우저에서 `http://localhost:5000`에 접속합니다. 끌 때는 `Ctrl+C` 또는 `docker compose down`입니다.

프로젝트 폴더가 컨테이너의 `/app`에 마운트되어 있어서 코드나 템플릿을 고치면 재빌드 없이 바로 반영됩니다.
`requirements.txt`를 바꿨을 때만 `--build`로 다시 빌드하세요.

### Docker 없이 실행

```bash
pip install -r requirements.txt
export COMFY_URL="http://<PC_IP>:8188"            # Windows cmd: set COMFY_URL=http://<PC_IP>:8188
export PUBLIC_COMFY_URL="http://<PC_IP>:8188"
python app2.py
```

---

## 3. VM 서버에 배포하기

UI(`templates/image.html`)나 코드를 수정한 뒤 VM 서버에 반영하고 웹에서 확인하는 절차입니다.

### 3-1. UI 수정

VS Code에서 `templates/image.html`을 수정하고 저장(`Ctrl+S`)합니다.

### 3-2. VM 서버로 복사 (scp)

**개발 컨테이너 터미널**(`root@...:/workspace/comfyui#`)에서 실행합니다.
`/workspace/comfyui`는 컨테이너 안의 경로입니다. PC cmd에서 실행할 때는 Windows 경로(예: `D:\dlproject\comfyui\...`)로 바꿔 쓰면 됩니다.

템플릿 파일만 업데이트:

```bash
scp /workspace/comfyui/templates/image.html <VM_USER>@<VM_IP>:~/comfyui/templates/
```

`app2.py`도 수정했다면:

```bash
scp /workspace/comfyui/app2.py <VM_USER>@<VM_IP>:~/comfyui/
```

프로젝트 전체를 다시 복사:

```bash
scp -r /workspace/comfyui <VM_USER>@<VM_IP>:~/
```

- 비밀번호를 입력할 때 화면에 글자가 보이지 않는 것은 정상입니다.
- 처음 접속할 때 `Are you sure you want to continue connecting?`가 나오면 `yes`를 입력합니다.
- `scp: command not found`가 나오면 컨테이너에 ssh 클라이언트를 설치합니다.
  ```bash
  apt update && apt install -y openssh-client
  ```

### 3-3. 처음 한 번만: VM 환경 준비

```bash
ssh <VM_USER>@<VM_IP>
cd ~/comfyui
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`venv` 생성이 실패하면 `sudo apt install -y python3-venv python3-pip`을 먼저 실행합니다.

### 3-4. VM 서버 실행 (PC cmd)

**PC의 cmd**에서 VM에 접속합니다.

```cmd
ssh <VM_USER>@<VM_IP>
```

접속한 뒤(프롬프트가 `<VM_USER>@...`로 바뀜) 서버를 실행합니다.
VM에는 `docker-compose.yml`의 설정이 적용되지 않으므로 **주소를 환경 변수로 지정**해야 합니다.

```bash
cd ~/comfyui
source venv/bin/activate
export COMFY_URL="http://<PC_IP>:8188"
export PUBLIC_COMFY_URL="http://<PC_IP>:8188"
python app2.py
```

`Running on http://<VM_IP>:5000`이 나오면 실행된 것입니다. 끌 때는 `Ctrl+C`를 누릅니다.

> 매번 `export`를 입력하기 귀찮다면 `~/.bashrc` 맨 아래에 두 `export` 줄을 추가해 두세요.

#### SSH 창을 닫아도 계속 실행하기

```bash
cd ~/comfyui
source venv/bin/activate
pkill -f app2.py                          # 이미 켜져 있으면 종료
nohup python app2.py > app.log 2>&1 &     # 백그라운드 실행
```

- 로그 보기: `tail -f ~/comfyui/app.log` (`Ctrl+C`로 보기 종료)
- 서버 끄기: `pkill -f app2.py`

#### PC cmd에서 한 줄로 재시작

VM에 들어가지 않고 PC cmd에서 바로 재시작할 수도 있습니다.

```cmd
ssh <VM_USER>@<VM_IP> "cd ~/comfyui && pkill -f app2.py; COMFY_URL=http://<PC_IP>:8188 PUBLIC_COMFY_URL=http://<PC_IP>:8188 nohup venv/bin/python app2.py > app.log 2>&1 < /dev/null &"
```

> 템플릿(`image.html`)만 바꿨다면 재시작하지 않아도 됩니다. `debug=True`라서 브라우저 새로고침만으로 반영됩니다. `app2.py`를 바꿨다면 재시작하세요.

### 3-5. 웹에서 확인

PC 브라우저에서 접속합니다.

```
http://<VM_IP>:5000
```

변경이 안 보이면 `Ctrl+F5`로 강력 새로고침합니다.

---

## 4. 문제 해결

| 증상 | 확인할 것 |
| --- | --- |
| `ssh`/`scp` 접속이 timeout | 학교 네트워크(교내망 또는 VPN)에 연결되어 있는지 |
| `Permission denied` | VM 계정 ID와 비밀번호 |
| 웹 페이지가 안 열림 | 서버가 실행 중인지 (`pgrep -f app2.py`), 포트 5000이 맞는지 |
| Generate 후 오류 / 시간 초과 | ComfyUI가 `--listen 0.0.0.0`으로 실행 중인지, 방화벽에서 8188 포트를 허용했는지, `COMFY_URL`이 맞는지 |
| ComfyUI 콘솔에 모델 관련 오류 | `models/checkpoints/`에 `sd_xl_turbo_1.0_fp16.safetensors`가 있는지 |
| 결과 이미지가 깨짐 | `PUBLIC_COMFY_URL`이 **브라우저에서** 열리는 주소인지 (F12 → Network 탭에서 `/view` 요청 확인) |
| `TemplateNotFound` | `templates/image.html`이 있는지, `app2.py`와 같은 폴더에서 실행했는지 |

ComfyUI 연결 확인 (Flask를 실행하는 곳에서):

```bash
python3 -c "import urllib.request as u;print(u.urlopen('http://<PC_IP>:8188/history',timeout=5).status)"
```

`200`이 나오면 정상입니다.
