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
        
        # [데이터 파싱 및 방어 로직]
        # 구글 API는 응답을 '상자 속의 상자'처럼 매우 깊은 중첩 JSON 구조로 줍니다.
        # (예: candidates -> content -> parts -> text)
        # ---------------------------------------------------------
        # [데이터 파싱 및 방어 로직 상세 설명]
        # 구글 Gemini API는 대답을 줄 때 다음과 같은 매우 복잡한(러시아 인형 같은) JSON 구조로 줍니다.
        # {
        #   "candidates": [                    <-- 후보군 리스트 (대답이 여러 개일 수 있어서 리스트 형태)
        #     {
        #       "content": {                   <-- 대답의 내용
        #         "parts": [                   <-- 구성 요소 리스트 (텍스트, 이미지 등이 섞일 수 있음)
        #           {
        #             "text": "진짜 AI 대답"   <-- 우리가 최종적으로 빼내고 싶은 진짜 알맹이!
        #           }
        #         ]
        #       }
        #     }
        #   ]
        # }
        # ---------------------------------------------------------
        
        # 1. 방어막: 응답 안에 'candidates(후보군)' 방이 있고, 그 방이 비어있지 않은지 검사합니다.
        # 이 검사를 통해 KeyError나 IndexError로 프로그램이 뻗는 것을 막습니다.
        # 1. 1차 방어막: 'candidates' 키가 존재하는지, 그리고 그 리스트가 비어있지 않은지 검사합니다.
        #    (구글 서버 오류나 차단 등으로 인해 빈 응답이 왔을 때 발생하는 KeyError, IndexError를 방지합니다.)
        if "candidates" in result_json and len(result_json["candidates"]) > 0:
            # 2. 껍질 까기: 중첩된 딕셔너리와 리스트를 파고들어 진짜 텍스트(알맹이)만 추출합니다.
            
            # 2. 껍질 까기: 위에서 설명한 JSON 구조를 따라 한 겹씩 인덱싱하며 들어갑니다.
            #    - ["candidates"][0] : 첫 번째 후보군 상자 열기
            #    - ["content"]       : 그 안의 내용물 상자 열기
            #    - ["parts"][0]      : 그 안의 첫 번째 구성요소 상자 열기
            #    - ["text"]          : 마침내 진짜 텍스트 추출!
            content = result_json["candidates"][0]["content"]["parts"][0]["text"]
            
            # 3. 다듬기: 텍스트 앞뒤에 묻어있는 불필요한 공백을 잘라내고(strip) 반환합니다.
            # 3. 마무리 다듬기: AI가 덧붙인 불필요한 줄바꿈(엔터)이나 앞뒤 공백을 strip()으로 깔끔하게 자르고 리턴합니다.
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
