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
    
    # 정규식으로 "commit_message": "내용" 추출 (AI가 예시를 말할 수 있으므로 마지막 매칭 사용)
    matches = re.findall(r'"commit_message"\s*:\s*"([^"]+)"', text)
    if matches:
        title = matches[-1].strip()
        # 만약 AI가 내부 생각으로 "..." 이라고 적은 걸 잡았다면 그 전 것을 씀
        if title == "..." and len(matches) > 1:
            title = matches[-2].strip()
    else:
        # JSON 추출 실패 시, 첫 줄 백업
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        title = lines[0] if lines else "chore: 코드 변경사항 업데이트"
        
    # 72자 제한
    if len(title) > 72:
        title = title[:69] + "..."
        
    return title

import re

def post_process_pr(text: str) -> str:
    """PR 메시지 후처리: 텍스트 긁어오기(다중 Fallback)"""
    # 방어 1단계: 마크다운 찌꺼기 청소
    text = text.replace("```text", "").replace("```markdown", "").replace("```", "").strip()
    
    title_match = re.search(r'(?i)(?:\[PR 제목\]|\*?\*?Title:\*?\*?)\s*(.*?)$', text, re.MULTILINE)
    why_match = re.search(r'(?i)(?:##\s*Why|\*?\*?Why:\*?\*?)\s*(.*?)(?=(?:##\s*What|\*?\*?What:\*?\*?)|$)', text, re.DOTALL)
    what_match = re.search(r'(?i)(?:##\s*What|\*?\*?What:\*?\*?)\s*(.*?)(?=(?:##\s*How to Test|\*?\*?How to Test:\*?\*?)|$)', text, re.DOTALL)
    how_match = re.search(r'(?i)(?:##\s*How to Test|\*?\*?How to Test:\*?\*?)\s*(.*?)(?=\n\*|\n\n|$)', text, re.DOTALL)
    
    # 긁어모은 파편(match 객체)들을 우리가 원하는 완벽한 한글 양식(## Why 등)으로 다시 재조립합니다.
    if title_match and (why_match or what_match):
        title = title_match.group(1).strip()
        body = ""
        if why_match: body += "## Why\n" + why_match.group(1).strip() + "\n\n"
        if what_match: body += "## What\n" + what_match.group(1).strip() + "\n\n"
        if how_match: body += "## How to Test\n" + how_match.group(1).strip()
        return f"[PR 제목]\n{title}\n\n[PR 본문]\n{body.strip()}"
        
    # 최후의 보루: 모든 전략이 실패했을 경우 원본 텍스트라도 사용자에게 보여줍니다.
    return "[추출 실패] 원본 텍스트:\n" + text
