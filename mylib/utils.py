# mylib/utils.py

import json
import os

def load_progress(filename: str) -> int:
    """
    이전에 크롤링이 정상 종료된 마지막 인덱스를 저장한 JSON 파일을 읽어서 반환합니다.
    - 파일이 없으면  -1 을 반환 (아직 아무것도 완료된 게 없음).
    """
    if not os.path.exists(filename):
        return -1
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_index", -1)
    except Exception:
        return -1

def save_progress(filename: str, last_index: int):
    """
    마지막으로 성공적으로 완료된 인덱스를 JSON 파일에 저장합니다.
    """
    tmp = {"last_index": last_index}
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tmp, f, ensure_ascii=False, indent=2)
