import argparse
import sys
import re
import pyperclip
import subprocess
from git_utils import get_git_status, get_git_diff
from ai_client import generate_text
from prompt_builder import build_commit_prompt, build_pr_prompt, post_process_commit, post_process_pr

def apply_safe_mode(diff_text: str) -> str:
    """안전 모드: 민감 정보 마스킹 및 전송량 제한 검사"""
    # 1. 마스킹 (이메일 및 sk- 로 시작하는 키 패턴)
    diff_text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***MASKED_EMAIL***', diff_text)
    diff_text = re.sub(r'sk-[a-zA-Z0-9]{20,}', '***MASKED_API_KEY***', diff_text)
    diff_text = re.sub(r'AI_API_KEY=[^\s]+', 'AI_API_KEY=***MASKED***', diff_text)
    
    # 2. 전송량 제한 검사
    lines = diff_text.split('\n')
    if len(lines) > 200:
        print("[ERROR] Safe Mode 제한: 변경 사항이 200줄을 초과하여 API 전송을 차단합니다.")
        sys.exit(1)
        
    file_count = diff_text.count("diff --git")
    if file_count > 10:
        print("[ERROR] Safe Mode 제한: 변경된 파일이 10개를 초과하여 API 전송을 차단합니다.")
        sys.exit(1)
        
    return diff_text

def main():
    parser = argparse.ArgumentParser(description="AI Git Assistant (커밋 및 PR 초안 자동 생성기)")
    subparsers = parser.add_subparsers(dest="command", help="실행할 명령어 (commit 또는 pr)")
    
    # 공통 옵션
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-model", type=str, default="gemma-4-26b-a4b-it", help="사용할 AI 모델")
    parent_parser.add_argument("-temperature", type=float, default=0.7, help="Temperature 값 (0.0 ~ 1.0)")
    parent_parser.add_argument("-max-tokens", type=int, default=1024, help="최대 생성 토큰 수")
    parent_parser.add_argument("-safe-mode", action="store_true", help="안전 모드 (민감 정보 마스킹 및 크기 제한)")
    
    # 서브커맨드 등록
    subparsers.add_parser("commit", parents=[parent_parser], help="커밋 메시지 자동 생성")
    subparsers.add_parser("pr", parents=[parent_parser], help="PR 초안 자동 생성")
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
        
    # 1. Git 상태 및 Diff 수집
    status_text = get_git_status()
    diff_text = get_git_diff()
    
    status_lines = len([line for line in status_text.split('\n') if line.strip()])
    diff_lines = len(diff_text.split('\n')) if diff_text else 0
    
    print(f"[INFO] Git status 수집 완료: {status_lines}개 파일 변경 감지")
    print(f"[INFO] Git diff 수집 완료: {diff_lines}줄")
    
    # 2. Safe Mode 적용
    if args.safe_mode:
        print("[INFO] Safe Mode 켜짐: 민감 정보 마스킹 및 파일 크기 검증 수행...")
        diff_text = apply_safe_mode(diff_text)
        
    # 3. 프롬프트 생성
    if args.command == "commit":
        prompt = build_commit_prompt(status_text, diff_text)
    else:
        # PR 명령어일 경우 브랜치 정보 출력
        branch_res = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, encoding='utf-8')
        print(f"[INFO] 현재 브랜치: {branch_res.stdout.strip()}")
        prompt = build_pr_prompt(status_text, diff_text)
        
    # 4. Google AI Studio API 호출
    raw_response = generate_text(prompt, model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
    
    # 5. 후처리 및 결과 출력
    if args.command == "commit":
        final_text = post_process_commit(raw_response)
        print("\n[DONE] 커밋 메시지 생성 완료")
    else:
        final_text = post_process_pr(raw_response)
        print("\n[DONE] PR 초안 생성 완료")
        
    print("==================================================")
    print(final_text)
    print("==================================================")
        
    # 6. 클립보드 자동 copy
    try:
        pyperclip.copy(final_text)
        print("[SUCCESS] 클립보드에 자동 복사되었습니다. Ctrl+V로 붙여넣으세요!")
    except Exception as e:
        print(f"[WARN] 클립보드 자동 복사 기능을 사용할 수 없습니다: {e}")

if __name__ == "__main__":
    main()

# TODO: 향후에는 이 CLI 도구를 GUI 환경(예: Tkinter, PyQt)과 연동하여 사용자가 버튼 클릭만으로 커밋과 PR을 생성할 수 있도록 확장할 예정입니다.
# 또한 사용자별 프롬프트 커스텀 기능과 다국어 지원(영어, 일본어 등)을 추가하여 글로벌 유저들도 사용할 수 있게 고도화해야 합니다.
