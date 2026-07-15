# AI Git Assistant (AI 기반 Git 커밋 & PR 자동 생성기)

AI(Gemma 4 26B)를 활용하여 터미널에서 Git 변경 사항을 분석하고, 적절한 커밋 메시지와 Pull Request 양식을 자동으로 생성해 주는 CLI 도구입니다.

## 과제 목표 (학습 내용)

이 프로젝트를 수행하며 다음 5가지 핵심 기술적 원리를 이해하고 구현했습니다.

### 1. REST API 연동 전체 흐름 (기술적 관점)
*   **요청 구성 (Request)**: `Endpoint URL`로 `POST` 메서드를 호출합니다. 이때 `Headers`에 `Content-Type: application/json`과 `Authorization: Bearer {API_KEY}`로 인증 정보를 담고, `Body`에 프롬프트와 파라미터를 JSON 형태로 직렬화(Serialization)하여 전송하는 구조를 설계합니다.
*   **응답 처리 (Response)**: 서버에서 응답받은 순수 JSON 스트링을 역직렬화(Deserialization)하여 파이썬 딕셔너리로 변환하고, 깊게 중첩된 데이터 구조(예: `response['candidates'][0]['content']['parts'][0]['text']`)에서 필요한 텍스트 노드만 정확히 파싱(Parsing)해내는 방법을 다룹니다.
*   **예외 대응 (Exception Handling)**: `try-except` 블록을 활용해 HTTP 상태 코드를 세밀하게 검증합니다. 401(토큰 오류), 429(호출 한도 초과), 500(서버 에러) 등 각 상황별로 분기하여, 프로그램이 뻗어버리지 않고 유저에게 원인과 조치 방법을 안내하는 방어적 프로그래밍(Defensive Programming) 흐름을 구성합니다.

### 2. `temperature`, `max_tokens` 주요 파라미터의 역할
*   **Temperature (온도)**: 모델의 출력 확률 분포를 평탄화하거나 날카롭게 만들어 응답의 무작위성(Randomness)을 제어하는 파라미터입니다. 값이 낮을수록 가장 확률이 높은 단어만 일관되게 선택하여 정형화된 커밋 메시지 생성에 적합하며, 값이 높을수록 다양한 어휘를 선택해 창의적인 결과를 도출합니다.
*   **Max Tokens (최대 토큰)**: 모델이 한 번의 요청에서 생성할 수 있는 최대 토큰(단어 조각) 수를 엄격하게 제한(Hard Limit)합니다. 불필요하게 긴 응답으로 인한 토큰 초과 오류나 리소스 낭비를 방지하는 역할을 합니다.

### 3. Git 명령어 실행 결과의 프로그램 입력 연결 및 자동화 흐름
*   **프로세스 통신과 캡처**: 파이썬의 `subprocess` 모듈을 사용해 자식 프로세스(Child Process)를 생성하고 `git diff` 명령어를 실행시킵니다. 이때 터미널(화면)로 나갈 표준 출력(stdout) 데이터를 화면에 뿌리지 않고, 파이썬 메모리로 직접 파이프라인을 연결해 가로챕니다(Capture).
*   **데이터 정제**: 가로챈 바이트(Bytes) 데이터를 UTF-8 문자열로 디코딩합니다.
*   **자동화 파이프라인**: 이렇게 디코딩된 순수 Diff 텍스트를 AI에 전송할 프롬프트 문자열의 동적 변수(`f-string`)로 주입(Injection)합니다. 즉, 유저가 마우스로 복사/붙여넣기 할 필요 없이 **[OS 명령 실행 ➔ 결과 캡처 ➔ 텍스트 정제 ➔ API 전송]**으로 이어지는 단방향 데이터 자동화 파이프라인을 구축하는 원리입니다.

### 4. 요구사항에 맞는 요약을 생성하는 프롬프트 구성 원리
*   **역할 및 컨텍스트 부여 (System Prompting)**: 모델에게 "너는 10년 차 시니어 개발자다" 같은 페르소나를 부여해 응답의 톤앤매너를 고정합니다.
*   **엄격한 출력 제약 (Formatting Constraints)**: PR 템플릿(Why, What, How to Test)을 마크다운 구조로 정확히 명시하고, "인사말이나 코드 블록 기호(```)를 쓰지 마라"는 규칙을 걸어 파이썬 프로그램이 후처리를 쉽게 할 수 있도록 AI의 출력을 통제합니다.
*   **데이터 캡슐화 (Context Injection)**: 3번에서 수집한 `git diff` 문자열을 `"""` 나 `<diff>` 같은 명확한 구분자(Delimiter)로 감싸서(캡슐화) 제공합니다. 이를 통해 AI가 엉뚱한 말(환각 현상)을 지어내지 않고, 오직 제공된 변경 맥락(Context) 데이터 안에서만 요약을 수행하도록 통제하는 원리를 배웁니다.

### 5. 텍스트 검증 및 다듬기 (후처리 및 QA)
*   **실무 규칙 적용**: 생성된 결과물이 실무의 엄격한 규칙(예: 커밋 제목 50자 이내)을 만족하는지 파이썬 코드로 검증(Validation)합니다. `len()` 함수를 사용한 문자열 길이 측정이나 정규식을 이용한 템플릿 구조 확인 등이 포함됩니다.
*   **문자열 정제 (Sanitization)**: AI가 규칙을 위반하고 마크다운 코드 블록이나 불필요한 공백을 반환할 경우, `.strip()`, `.replace()` 또는 정규식을 통해 결과물을 강제로 규격에 맞게 깎아내는(Trimming) 방어적 후처리 과정을 거쳐 최종 결과의 신뢰성을 보장합니다.

## 💡 FAQ 및 실무 팁 (Troubleshooting & Tips)

### 1. 루트 디렉토리(Root Directory) vs 홈 디렉토리(Home Directory)
*   **루트 디렉토리 (Project Root)**: 이 프로젝트의 가장 꼭대기(최상단) 폴더를 말합니다. Git의 관점에서는 `.git`이라는 숨김 폴더가 생성되어 있는 바로 그 위치입니다.
*   **홈 디렉토리 (Home)**: 내 컴퓨터 사용자(User)의 개인 앞마당(예: `C:\Users\Username`)입니다. 
*   **왜 루트에서 실행해야 할까?**: 파이썬 프로그램이 내부적으로 `git status` 명령어를 실행할 때, Git 저장소가 아닌 곳에서 실행하면 에러가 발생합니다. 따라서 프로젝트 전체의 변경 사항을 빠짐없이 스캔하려면 반드시 이 프로젝트를 총괄하는 루트 폴더에서 스크립트를 실행해야 합니다.

### 2. `git status`와 `git diff`의 차이점
*   **`git status`**: "어떤 파일들이" 변경(수정, 생성, 삭제)되었는지 그 **파일들의 이름과 상태(목록)**만 수집합니다.
*   **`git diff`**: 파일 속으로 들어가서 "정확히 몆 번째 줄의 어떤 코드가 +추가되고 -삭제되었는지" **상세한 코드 텍스트(내용)**를 수집합니다.

### 3. "변경 사항이 없을 시 스크립트 종료"의 의미
터미널 창이나 컴퓨터가 꺼진다는 뜻이 아닙니다. Git으로 코드 변경 사항을 확인했을 때 수정된 내용이 없다면 AI에게 보낼 데이터 자체가 없으므로, 불필요한 API 호출(무료 한도 낭비)을 막기 위해 **실행된 파이썬 스크립트(`main.py`)만 조기 종료(`sys.exit(0)`)**한다는 의미입니다.

### 4. 커밋 본문 생략 전략
명세서 상 커밋 본문 포함 여부는 선택 사항입니다. 본문을 포함할 경우 "바뀐 파일 1~3개 언급", "불릿 기호 사용" 등의 조건을 파이썬 코드로 일일이 검증(QA)해야 하는 복잡성이 생깁니다. 따라서 가장 효율적으로 구현하는 방법은 **깔끔하게 커밋 제목 1줄만 생성하도록** 구현하는 것입니다.

### 5. 초안(Draft) 텍스트의 의미
AI가 쓴 글을 사람의 확인 없이 곧바로 깃허브에 올려버리면(자동 Push) 예기치 못한 사고가 발생할 수 있습니다. 그래서 이 도구는 터미널에 **"초안(Draft)"**을 출력하는 역할까지만 수행하며, 최종 검토 및 깃허브 반영은 사용자가 직접 수행합니다.

### 6. 자동 복사 기능 (`pyperclip`)
터미널에서 마우스로 드래그하여 복사하는 번거로움을 줄이기 위해, 파이썬의 `pyperclip` 라이브러리를 활용합니다. AI가 생성한 결과물이 터미널에 출력됨과 동시에 클립보드에 자동으로 복사되므로 즉시 `Ctrl + V`로 붙여넣어 사용할 수 있습니다.

### 7. 불릿(Bullet)과 출력 포매팅
*   **불릿**: 마크다운 문법에서 `-` 기호나 `*` 기호를 써서 요점만 나열하는 리스트(List) 형태의 글머리 기호를 뜻합니다.
*   **구분선 포매팅**: 밋밋한 텍스트 덩어리를 방지하기 위해 터미널 출력 시 `==========` 같은 기호와 헤더 영역을 나누어 시각적인 가독성을 높입니다.

### 8. 출력 형식 검증: 재생성 vs 후처리
글자 수 제한 등을 위반했을 때, AI API를 다시 호출하는 '재생성' 방식은 시간과 API 비용이 낭비됩니다. 따라서 파이썬의 문자열 슬라이싱(`title[:72]`) 등을 활용하여 코드 단에서 즉시 결과물을 다듬는 **'후처리'** 방식이 훨씬 경제적이고 구현이 쉽습니다.

### 9. "결과물은 push 되어 있어야 한다"의 진짜 의미
우리 프로그램이 자동으로 원격 저장소에 `git push`를 하라는 의미가 **절대 아닙니다**. 명세서의 제약 사항에 따라 자동 push 기능 구현은 금지되어 있습니다. 이 문구는 단순히 **"완성된 파이썬 소스 코드 결과물을 깃허브에 올려서 숙제로 제출하라"**는 의미입니다.

### 10. 마스킹 / 제외 / 안전 모드(Safe Mode)란?
개인정보나 API 키가 구글(AI 서버)로 유출되는 것을 막기 위한 방어막입니다.
*   **마스킹(Masking)**: 정규식을 사용해 코드 안의 이메일이나 API 키 형태를 찾아 `***MASKED***`로 안전하게 치환하는 기능입니다.
*   **제외(Exclusion)**: `.env` 파일처럼 비밀번호가 들어있을 확률이 높은 파일은 아예 `git diff` 목록에서 제외해 버리거나, 변경된 코드가 200줄이 넘어가면 전송 자체를 차단하는 기능입니다.

## 설치 및 실행 가이드

### 1. 패키지 설치
이 프로젝트는 파이썬 기본 내장 모듈(`subprocess`, `sys`, `os` 등) 외에 API 통신과 자동 복사 기능을 위한 외부 패키지를 사용합니다.
```bash
pip install -r requirements.txt
```

### 2. 환경변수(API Key) 설정 및 발급 방법

**🔑 API 키 발급받기**
1. [Google AI Studio](https://aistudio.google.com/)에 접속하여 구글 계정으로 로그인합니다.
2. 좌측 메뉴에서 **[Get API key]** (또는 열쇠 모양 아이콘)를 클릭합니다.
3. **[Create API key]** 버튼을 눌러 새로운 키를 생성하고 복사합니다. (무료입니다!)

**🔒 안전하게 저장하기 (.env 파일 방식)**
매번 터미널에 키를 입력하는 번거로움을 없애기 위해, 실무 표준 방식인 `.env` 파일을 사용합니다.

1. 프로젝트 최상위 폴더에 `.env` 라는 이름의 메모장 파일을 만듭니다. (확장자 없이 이름 자체가 `.env` 입니다)
2. 파일 안에 방금 복사한 키를 아래와 같이 붙여넣고 저장합니다.
   ```env
   AI_API_KEY="AIzaSy...여기에_복사한_키_붙여넣기"
   ```
*(주의: 이 저장소에는 이미 `.gitignore`가 설정되어 있어 여러분의 `.env` 파일이 깃허브로 절대 유출되지 않으니 안심하셔도 됩니다!)*

### 3. 커밋/PR 자동 생성 명령 사용 예시 및 결과 화면

#### 커밋 메시지 자동 생성
```bash
python main.py commit
```
**터미널 출력 예시:**
```text
[INFO] Git status 수집 완료: 3개 파일 변경 감지
[INFO] Git diff 수집 완료: 128줄
[INFO] AI API 요청 중... (API 호출 횟수: 1회)

[DONE] 커밋 메시지 생성 완료
==================================================
feat: Git 변경 사항 기반 커밋 메시지 자동 생성 기능 추가
==================================================
💡 (클립보드에 자동 복사되었습니다. Ctrl+V로 붙여넣으세요!)
```

#### PR 제목/본문 자동 생성
```bash
python main.py pr
```
**터미널 출력 예시:**
```text
[INFO] 현재 브랜치: feature/commit-pr-generator
[INFO] AI API 요청 중... (API 호출 횟수: 1회)

[DONE] PR 초안 생성 완료
==================================================
[PR 제목]
feat: 커밋/PR 자동 생성 기능 추가

[PR 본문]
## Why
- 팀 협업 시 커밋 메시지와 PR 설명 작성에 시간이 소요되어 자동 생성 도구가 필요했습니다.
- Git 변경 사항을 기반으로 일관된 형식의 요약 텍스트를 생성해 리뷰 효율을 높이고자 했습니다.

## What
- git status, git diff 결과를 수집해 AI 입력 컨텍스트로 전달하는 로직 추가
- 커밋 메시지 자동 생성 기능(python main.py commit) 구현
- PR 제목/본문 자동 생성 기능(python main.py pr) 및 템플릿 적용
- API Key 누락/요청 실패 시 에러 메시지 및 예외 처리 개선

## How to Test
- 환경변수 설정: export AI_API_KEY="YOUR_KEY"
- 커밋 메시지 생성: python main.py commit
- PR 초안 생성: python main.py pr
- 결과로 출력된 PR 본문이 Why/What/How to Test 구조와 길이 규칙을 만족하는지 확인
==================================================
💡 (클립보드에 자동 복사되었습니다. Ctrl+V로 붙여넣으세요!)
```

#### 예외 상황 1: AI API Key 미설정/오류 시
```bash
python main.py commit
```
**터미널 출력 예시:**
```text
[ERROR] AI_API_KEY 환경변수가 설정되지 않았습니다.
## 예) export AI_API_KEY="YOUR_KEY"
```

#### 예외 상황 2: 변경 사항이 없는 경우
```bash
python main.py commit
```
**터미널 출력 예시:**
```text
[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 조기 종료합니다.
```

---

## 🛠️ AI Git Assistant 개발 트러블슈팅(Troubleshooting) 히스토리

회사 분들에게 공유하기 좋도록, 우리가 처음부터 겪었던 문제점들과 원인, 그리고 그것을 어떻게 해결해 왔는지 Before/After 코드와 함께 시간순으로 정리했습니다.

### Phase 1: 첫 커밋 시 `git diff` 증발 문제
- **기대했던 결과:** 갓 생성한 프로젝트의 400줄이 넘는 코드를 AI에게 전달하여 분석하게 하는 것.
- **발생한 문제:** `python main.py commit`을 처음 실행했을 때, `[INFO] Git diff 수집 완료: 0줄`이 떴습니다. 
- **원인:** Git은 원래 `HEAD`(이전 커밋)와 현재 상태를 비교(diff)합니다. 하지만 **프로젝트의 가장 첫 커밋**은 비교할 대상(이전 커밋)이 아예 존재하지 않아 에러가 나거나 빈 값을 반환합니다.
- **해결 방법:** `git_utils.py`에 예외 처리 로직을 추가하여, 이전 커밋이 없을 경우 Git 내부적으로 존재하는 **'빈 트리(Empty Tree)의 해시값'**과 강제 비교하도록 우회(Fallback)했습니다.

**[Before]** (`git_utils.py`)
```python
# 단순히 HEAD와 캐시된 변경점 비교 (첫 커밋 시 실패)
diff_res = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True)
return diff_res.stdout.strip()
```

**[After]** (`git_utils.py`)
```python
# HEAD 존재 여부를 먼저 확인하고, 없으면 Empty Tree Hash를 사용
head_check = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
if head_check.returncode != 0:
    empty_tree_hash = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    diff_res = subprocess.run(['git', 'diff', '--cached', empty_tree_hash], capture_output=True, text=True, encoding='utf-8')
else:
    diff_res = subprocess.run(['git', 'diff', '--cached'], capture_output=True, text=True, encoding='utf-8')
```

---

### Phase 2: AI의 "역할극(Role-Playing) 과몰입" 현상
- **기대했던 결과:** `feat: 초기 세팅` 같은 깔끔한 커밋 메시지 딱 1줄.
- **발생한 문제:** AI가 자꾸 `* Role: 10-year Senior Developer. * Input: git status...` 라며 장황하게 상황 설명을 늘어놓았습니다.
- **원인:** 초기 프롬프트에 "당신은 10년 차 시니어 개발자입니다"라는 페르소나를 부여했더니, AI가 역할극에 과몰입하는 할루시네이션이 발생했습니다.
- **해결 방법:** 역할극 문구를 아예 삭제하고, **Few-Shot(예시 훈련)** 기법을 도입하여 구체적인 입출력 예시를 강제했습니다.

**[Before]** (`prompt_builder.py`)
```python
return f"""당신은 10년 차 시니어 개발자입니다. 
아래의 git status와 git diff 결과를 분석하여 가장 적절한 커밋 메시지 제목을 작성하세요.
..."""
```

**[After]** (`prompt_builder.py`)
```python
return f"""아래의 git status와 git diff 결과를 분석하여 가장 적절한 커밋 메시지 제목을 작성하세요.

[예시]
입력: (로그인 API 추가된 코드)
출력: feat: 로그인 API 연동 및 인증 로직 구현
..."""
```

---

### Phase 3: 윈도우 인코딩 크래시 (이모지 에러)
- **기대했던 결과:** 💡 이모지와 함께 "클립보드에 복사되었습니다" 메시지가 출력되는 것.
- **발생한 문제:** 윈도우 터미널이 `UnicodeEncodeError`를 뿜으며 스크립트가 뻗어버렸습니다.
- **원인:** 윈도우의 기본 터미널(CP949)이 파이썬이 출력하려는 전구 이모지(💡)를 인식하지 못했습니다.
- **해결 방법:** 이모지를 윈도우 친화적인 영어 텍스트로 대체했습니다.

**[Before]** (`main.py`)
```python
print("💡 (클립보드에 자동 복사되었습니다. Ctrl+V로 붙여넣으세요!)")
```

**[After]** (`main.py`)
```python
print("[SUCCESS] 클립보드에 자동 복사되었습니다. Ctrl+V로 붙여넣으세요!")
```

---

### Phase 4: 커밋 메시지 포맷팅 고집과 JSON 강제화
- **기대했던 결과:** AI가 `feat: ~` 형태의 1줄짜리 커밋 메시지만 뱉어내는 것.
- **발생한 문제:** 400줄이 넘는 코드를 던져주자, AI가 1줄 요약을 무시하고 `* git status: Shows new files...` 라며 영문 코드 리뷰를 출력했습니다.
- **원인:** 대형 언어 모델(`Gemma 4 26B`)이 지시사항보다 방대한 텍스트를 요약하고 싶어 하는 본능(Chain of Thought)이 발동했습니다.
- **해결 방법:** 프롬프트를 **JSON 포맷**으로 강제하고, 파이썬에 **정규식(Regex) 파서**를 달아 JSON 껍데기 안의 밸류(Value)만 강제로 뜯어왔습니다.

**[Before]** (`prompt_builder.py`)
```python
[규칙]
1. 인삿말, 역할 설명, 과정 등은 절대 적지 마세요.
2. 커밋 본문 없이 오직 제목 1줄만 출력하세요.
```

**[After]** (`prompt_builder.py`)
```python
[필수 규칙]
반드시 아래의 JSON 포맷으로만 응답해야 하며, 다른 기호는 추가하지 마세요.
{{
  "commit_message": "chore: 초기 프로젝트 구조 설정 및 필수 파일 추가"
}}
```
```python
# 파이썬 파싱 로직 추가
match = re.search(r'"commit_message"\s*:\s*"([^"]+)"', text)
if match:
    title = match.group(1).strip()
```

---

### Phase 5: PR 생성 시 발생한 '자기 참조(Quine) 버그'와 불도저식 다중 Fallback
- **기대했던 결과:** 마크다운 형태의 예쁜 PR 초안(Title, Why, What, How to Test) 텍스트 추출.
- **발생한 문제:** AI의 헛소리를 자르기 위해 파이썬 코드에 `===TITLE===` 같은 구분 기호를 넣었으나 파싱 로직이 완전히 붕괴되었습니다.
- **원인 (자기 참조 버그):** 파이썬 코드에 방금 추가한 기호가 `git diff`(코드 변경점) 안에 그대로 포함되어 AI에게 전달되었고, AI가 그 기호를 발견하고는 엉뚱한 맥락에 출력하여 `.split()` 로직을 박살 냈습니다.
- **해결 방법 (불도저식 스크래핑 도입):**
    AI의 출력 포맷을 통제하는 것을 포기하고, **어떻게 뱉어내든 강제로 뜯어오는 다중 정규식 덫**을 설치했습니다. AI가 제멋대로 영문 키워드(`*Title:*`, `*Why:*`)를 출력하더라도, 이를 감지해서 우리가 원하는 한국어 템플릿(`## Why`)으로 강제 재조립합니다.

**[Before]** (`prompt_builder.py`)
```python
# 단순 무식한 자르기 (기호가 중복 등장하면 완벽하게 붕괴됨)
if "===TITLE===" in text and "===BODY===" in text:
    title_part = text.split("===TITLE===")[1].split("===BODY===")[0].strip()
```

**[After]** (`prompt_builder.py`)
```python
# 다중 Fallback 정규식 스크래핑 (AI가 어떤 양식으로 뱉어내든 강제 추출 후 조립)
title_match = re.search(r'(?i)\*?\*?Title:\*?\*?\s*(.*?)$', text, re.MULTILINE)
why_match = re.search(r'(?i)\*?\*?Why:\*?\*?\s*(.*?)(?=\*?\*?What:|$)', text, re.DOTALL)
what_match = re.search(r'(?i)\*?\*?What:\*?\*?\s*(.*?)(?=\*?\*?How to Test:|$)', text, re.DOTALL)
how_match = re.search(r'(?i)\*?\*?How to Test:\*?\*?\s*(.*)', text, re.DOTALL)

if title_match and (why_match or what_match):
    title = title_match.group(1).strip()
    body = ""
    if why_match: body += "## Why\n" + why_match.group(1).strip() + "\n\n"
    # (한국어 템플릿으로 강제 재조립)
```

---
**🏆 최종 결론:** 
단순히 구글 AI API를 연결한 스크립트가 아니라, **AI의 할루시네이션(헛소리), 장황한 사고 과정(Chain of Thought), 그리고 초기 커밋이나 인코딩 에러 같은 로컬 환경의 돌발 변수까지 모두 엔지니어링으로 억눌러 통제한 진정한 의미의 CLI 비서**가 완성되었습니다.
