# app2.py
from flask import Flask, request, render_template
import requests, json, time, os, random

# ---------- 환경 설정 ----------
#  아래 주소는 환경 변수로 설정합니다. (docker-compose.yml 의 environment 또는 셸에서 export)
#    환경 변수가 없으면 기본값이 사용되므로, 기본값을 "본인 PC의 IP 주소"로 바꿔서 사용하세요.
#    예) ComfyUI를 192.168.0.10 PC에서 실행 중이라면 → "http://192.168.0.10:8188"

# Flask 서버가 ComfyUI API(/prompt, /history)를 호출할 때 쓰는 주소

COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")  # ← 본인 PC(ComfyUI 실행 PC) IP로 변경
'''
COMFY_URL = os.getenv("COMFY_URL", "http://-----------") #다른 PC의 Comfy UI추론 실행 테스트 확인용
'''
# 브라우저가 결과 이미지(/view)를 직접 불러올 때 쓰는 주소
#   - 브라우저에서 열리는 주소여야 합니다. (컨테이너 전용 주소 host.docker.internal 은 사용 불가)
#   - 설정하지 않으면 COMFY_URL 과 같은 값을 사용합니다.
PUBLIC_COMFY_URL = os.getenv("PUBLIC_COMFY_URL", COMFY_URL)  # ← 본인 PC IP로 변경

WORKFLOW_PATH = os.getenv("WORKFLOW_PATH", "./static/test.json")  # ComfyUI 워크플로(API 형식) JSON 경로
'''
WORKFLOW_PATH = os.getenv("WORKFLOW_PATH", "./static/flux2.json")
'''
PORT = int(os.getenv("PORT", "5000"))  # Flask 포트

app = Flask(__name__)

# ---------- 기능별 함수 ---------
def load_workflow(path: str) -> dict:
    """JSON 워크플로를 파일에서 읽기"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Workflow not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def update_prompts(graph: dict, pos: str, neg: str,
                    pos_node_id: str = "6", neg_node_id: str = "7") -> dict:
    graph["13"]["inputs"]["noise_seed"] = random.randint(0, 2**32 - 1) # 시드 랜덤화
    graph[pos_node_id]["inputs"]["text"] = pos
    graph[neg_node_id]["inputs"]["text"] = neg
    return graph
'''
def update_prompts(graph: dict, pos: str, neg: str,
                    pos_node_id: str = "76", neg_node_id: str = "75:67") -> dict:
    graph["75:73"]["inputs"]["noise_seed"] = random.randint(0, 2**32 - 1) # 시드 랜덤화
    graph[pos_node_id]["inputs"]["value"] = pos   # PrimitiveStringMultiline 은 "value"
    graph[neg_node_id]["inputs"]["text"] = neg
    return graph
'''

def submit_prompt(graph: dict) -> str:
    # ComfyUI /prompt 에 워크플로 제출 후 prompt_id 반환
    r = requests.post(f"{COMFY_URL}/prompt", json={"prompt": graph})
    r.raise_for_status()
    return r.json()["prompt_id"]

def poll_history(prompt_id: str, timeout_sec: int = 60, interval: float = 1.0) -> dict | None:
    """
    간단 폴링: /history/{prompt_id} 에서 완료 결과를 받을 때까지 대기
    """
    end = time.time() + timeout_sec
    while time.time() < end:
        h = requests.get(f"{COMFY_URL}/history/{prompt_id}")
        if h.status_code == 200 and h.json():
            return list(h.json().values())[0] # 해당 prompt의 히스토리 블록
        time.sleep(interval)
    return None

def extract_first_image_url(history_block: dict) -> str:
    """
    히스토리 블록에서 SaveImage 출력의 첫 번째 이미지를 view URL로 구성
    """
    if not history_block:
        return ""
    outputs = history_block.get("outputs", {})
    for node_id, node_out in outputs.items():
        if "images" in node_out and node_out["images"]:
            img = node_out["images"][0]
            fn = img.get("filename")
            sub = img.get("subfolder", "")
            t = img.get("type", "output")
            if fn:
                return f"{PUBLIC_COMFY_URL}/view?filename={fn}&subfolder={sub}&type={t}"
    return ""

# ---------- Flask 라우트 ---------
@app.route("/", methods=["GET", "POST"])
def index():
    pos = request.form.get("pos", "a beautiful landscape with galaxy in a bottle")
    neg = request.form.get("neg", "text, watermark")
    img_url = ""

    if request.method == "POST":
        graph = load_workflow(WORKFLOW_PATH)
        graph = update_prompts(graph, pos, neg) # 필요 시 노드 ID 인자 조정 가능
        prompt_id = submit_prompt(graph)
        history_block = poll_history(prompt_id)
        img_url = extract_first_image_url(history_block)
    return render_template("image.html", pos=pos, neg=neg, img_url=img_url)

if __name__ == "__main__":
    # pip install -r requirements.txt
    app.run(host="0.0.0.0", port=PORT, debug=True)
