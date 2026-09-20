import subprocess
import sys

def get_git_status() -> str:
    """git status 결과를 반환합니다. 변경 사항이 없으면 프로그램을 조기 종료합니다."""
    # 변경 사항 존재 여부 확인
    check_result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if not check_result.stdout.strip():
        print("[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 조기 종료합니다.")
        sys.exit(0)
    
    # 실제 프롬프트용 상세 상태 텍스트
    result = subprocess.run(['git', 'status'], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout.strip()

def get_git_diff() -> str:
    """git diff 결과를 반환합니다 (HEAD가 없는 최초 커밋 전 상태도 완벽 지원)."""
    # 1. HEAD 존재 여부 확인 (최초 커밋 전인지 확인)
    head_check = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], capture_output=True)
    if head_check.returncode != 0:
        # 최초 커밋 전이면 Git의 특수 '빈 트리(Empty Tree)' 해시를 사용
        target = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
    else:
        target = 'HEAD'
        
    result = subprocess.run(['git', 'diff', target], capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.stdout.strip()

def is_git_repository() -> bool:
    """현재 디렉토리가 Git 저장소인지 확인합니다."""
    try:
        subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'], 
                       capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def get_git_author() -> str:
    """현재 Git 설정된 사용자 이름을 반환합니다."""
    try:
        res = subprocess.run(['git', 'config', 'user.name'], 
                             capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError:
        return "Unknown Author"
