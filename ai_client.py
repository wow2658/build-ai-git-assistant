import os
import sys
import requests
import json
from dotenv import load_dotenv

def get_api_key() -> str:
    """환경변수에서 API Key를 가져옵니다. 없으면 에러 메시지를 출력하고 종료합니다."""
    load_dotenv() # .env 파일이 있으면 환경변수로 자동 로드
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        print('[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.')
        print('## 프로젝트 최상위 폴더에 .env 파일을 만들고 AI_API_KEY="본인의키" 형태로 입력하세요.')
        sys.exit(1)
    return api_key

def generate_text(prompt: str, model: str = "gemma-4-26b-a4b-it", temperature: float = 0.7, max_tokens: int = 1024) -> str:
    """Google AI Studio API를 호출하여 텍스트를 생성합니다."""
    api_key = get_api_key()
    
    # Google AI Studio API 엔드포인트
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    print(f"[INFO] AI API 요청 중... (API 호출 횟수: 1회)")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result_json = response.json()
        if "candidates" in result_json and len(result_json["candidates"]) > 0:
            content = result_json["candidates"][0]["content"]["parts"][0]["text"]
            return content.strip()
        else:
            print("[ERROR] API 응답 형식이 예상과 다릅니다.")
            print(result_json)
            sys.exit(1)
            
    except requests.exceptions.HTTPError as err:
        status_code = err.response.status_code
        if status_code == 400:
            print(f"[ERROR] 잘못된 요청입니다 (400). 모델 이름({model})이나 파라미터를 확인하세요.")
        elif status_code in (401, 403):
            print("[ERROR] 인증에 실패했습니다 (401/403). AI_API_KEY가 유효한지 확인하세요.")
        elif status_code == 429:
            print("[ERROR] 호출 한도를 초과했습니다 (429). 무료 티어 사용량을 확인하고 잠시 후 다시 시도하세요.")
        elif status_code >= 500:
            print(f"[ERROR] 서버 오류가 발생했습니다 ({status_code}).")
        else:
            print(f"[ERROR] API 호출 중 HTTP 오류 발생: {err}")
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print(f"[ERROR] 네트워크 통신 오류가 발생했습니다: {err}")
        sys.exit(1)
