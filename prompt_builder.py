import re

def build_commit_prompt(status_text: str, diff_text: str) -> str:
    return f"""아래의 git status와 git diff 결과를 분석하여 가장 적절한 커밋 메시지 제목을 작성하세요.

[필수 규칙]
반드시 아래의 JSON 포맷으로만 응답해야 하며, 그 외의 어떠한 설명이나 기호(```)도 추가하지 마세요.
커밋 메시지 제목은 Conventional Commits 형식(feat:, fix:, chore: 등)으로 시작해야 합니다.

{{
  "commit_message": "chore: 초기 프로젝트 구조 설정 및 필수 파일 추가"
}}

[Git Status]
{status_text}

[Git Diff]
{diff_text}
"""

def build_pr_prompt(status_text: str, diff_text: str) -> str:
    return f"""아래의 git status와 git diff 결과를 분석하여 Pull Request(PR) 초안을 작성하세요.

[규칙]
1. 인삿말, 역할 설명 등은 절대 적지 말고 바로 PR 내용만 출력하세요.
2. 마크다운 코드 블록(```)을 사용하지 마세요.
3. PR 제목과 본문을 아래 지정된 형식에 정확히 맞춰서 작성하세요.

[출력 형식]
[PR 제목]
(이곳에 80자 이내의 제목 1줄 작성)

[PR 본문]
## Why
- (변경한 이유를 불릿 포인트로 작성)

## What
- (무엇을 변경했는지 불릿 포인트로 작성)

## How to Test
- (어떻게 테스트할 수 있는지 불릿 포인트로 작성)

[Git Status]
{status_text}

[Git Diff]
{diff_text}

위 규칙과 출력 형식을 엄격하게 지켜서 즉시 PR 초안을 출력하세요:
"""

def post_process_commit(text: str) -> str:
    """커밋 메시지 후처리: JSON 파싱 및 최대 72자 제한 적용"""
    text = text.replace("```json", "").replace("```text", "").replace("```", "").strip()
    
    # 정규식으로 "commit_message": "내용" 추출
    match = re.search(r'"commit_message"\s*:\s*"([^"]+)"', text)
    if match:
        title = match.group(1).strip()
    else:
        # JSON 추출 실패 시, 첫 줄 백업
        lines = [line.strip() for line in text.split('\\n') if line.strip()]
        title = lines[0] if lines else "chore: 코드 변경사항 업데이트"
        
    # 72자 제한
    if len(title) > 72:
        title = title[:69] + "..."
        
    return title

def post_process_pr(text: str) -> str:
    """PR 메시지 후처리: 불필요한 기호 제거 및 정리"""
    text = text.replace("```text", "").replace("```markdown", "").replace("```", "").strip()
    return text
