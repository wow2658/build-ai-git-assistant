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
    return f"""당신은 PR 자동 생성 봇입니다. 
당신의 응답은 반드시 오직 아래의 양식으로만 구성되어야 하며, 다른 설명이나 분석 과정은 절대 출력하지 마세요.

[PR 제목]
(80자 이내의 PR 제목 작성)

[PR 본문]
## Why
- 변경 이유

## What
- 변경 내용

## How to Test
- 테스트 방법

[Git Status]
{status_text}

[Git Diff]
{diff_text}
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

import re

def post_process_pr(text: str) -> str:
    """PR 메시지 후처리: 텍스트 긁어오기(다중 Fallback)"""
    text = text.replace("```text", "").replace("```markdown", "").replace("```", "").strip()
    
    # 전략 1: 지정된 [PR 제목], [PR 본문] 포맷을 잘 따랐을 경우 (마지막 등장 기준)
    if "[PR 제목]" in text and "[PR 본문]" in text:
        title_idx = text.rfind("[PR 제목]")
        body_idx = text.rfind("[PR 본문]")
        if title_idx < body_idx:
            title = text[title_idx + len("[PR 제목]"):body_idx].strip()
            body = text[body_idx + len("[PR 본문]"):].strip()
            return f"[PR 제목]\n{title}\n\n[PR 본문]\n{body}"
            
    # 전략 2: AI가 맘대로 *Title:*, *Why:* 등의 영문 템플릿으로 출력했을 경우
    title_match = re.search(r'(?i)\*?\*?Title:\*?\*?\s*(.*?)$', text, re.MULTILINE)
    why_match = re.search(r'(?i)\*?\*?Why:\*?\*?\s*(.*?)(?=\*?\*?What:|$)', text, re.DOTALL)
    what_match = re.search(r'(?i)\*?\*?What:\*?\*?\s*(.*?)(?=\*?\*?How to Test:|$)', text, re.DOTALL)
    how_match = re.search(r'(?i)\*?\*?How to Test:\*?\*?\s*(.*)', text, re.DOTALL)
    
    if title_match and (why_match or what_match):
        title = title_match.group(1).strip()
        body = ""
        if why_match: body += "## Why\n" + why_match.group(1).strip() + "\n\n"
        if what_match: body += "## What\n" + what_match.group(1).strip() + "\n\n"
        if how_match: body += "## How to Test\n" + how_match.group(1).strip()
        return f"[PR 제목]\n{title}\n\n[PR 본문]\n{body.strip()}"
        
    return "[추출 실패] 원본 텍스트:\n" + text
