"""Tự động commit + push thay đổi trong 'Dữ liệu thô' lên GitHub.

Chỉ chạy khi có secret/biến môi trường GITHUB_TOKEN — nếu không có (ví dụ khi
chạy local mà chưa cấu hình), bỏ qua lặng lẽ và không ảnh hưởng gì tới luồng
cập nhật dữ liệu chính. Dùng để bù đắp việc filesystem của Streamlit Community
Cloud là tạm thời: sau khi lưu CSV mới, đẩy luôn về GitHub để không mất dữ
liệu khi app cloud khởi động lại.

Cách bật trên Streamlit Cloud: App settings > Secrets, thêm dòng
    GITHUB_TOKEN = "ghp_xxx..."
Token cần quyền ghi (contents: write / scope "repo") vào đúng repo đang deploy.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR_NAME = "Dữ liệu thô"


def _get_token() -> str | None:
    try:
        import streamlit as st

        token = st.secrets.get("GITHUB_TOKEN")
        if token:
            return str(token)
    except Exception:
        pass
    return os.environ.get("GITHUB_TOKEN")


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, timeout=30)


def sync_data_dir(commit_message: str) -> str:
    """Commit + push thay đổi trong thư mục dữ liệu lên nhánh hiện tại.

    Không raise lỗi ra ngoài — mọi thất bại trả về dưới dạng chuỗi mô tả,
    không chặn luồng cập nhật dữ liệu chính. Trả về "skip" nếu chưa cấu hình
    GITHUB_TOKEN (ví dụ đang chạy local).
    """
    token = _get_token()
    if not token:
        return "skip"

    try:
        remote = _run(["git", "remote", "get-url", "origin"])
        if remote.returncode != 0:
            return "Không tìm thấy remote 'origin', bỏ qua đồng bộ."
        origin_url = remote.stdout.strip()
        if not origin_url.startswith("https://") or "@" in origin_url:
            return "Remote không ở dạng https:// hỗ trợ, bỏ qua đồng bộ tự động."
        auth_url = origin_url.replace("https://", f"https://x-access-token:{token}@", 1)

        _run(["git", "add", DATA_DIR_NAME])
        status = _run(["git", "status", "--porcelain", "--", DATA_DIR_NAME])
        if not status.stdout.strip():
            return "Không có thay đổi dữ liệu để đồng bộ."

        commit = _run(
            [
                "git",
                "-c", "user.email=streamlit-cloud@bot.local",
                "-c", "user.name=Streamlit Cloud Bot",
                "commit", "-m", commit_message, "--", DATA_DIR_NAME,
            ]
        )
        if commit.returncode != 0:
            return f"Lỗi khi commit: {commit.stderr.strip()[:300]}"

        branch_res = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch_res.stdout.strip() or "main"

        push = _run(["git", "push", auth_url, f"HEAD:{branch}"])
        if push.returncode != 0:
            err = push.stderr.replace(token, "***").strip()
            return f"Đã commit ở bản cloud nhưng push thất bại: {err[:300]}"

        return "Đã đồng bộ dữ liệu mới lên GitHub."
    except Exception as e:  # đồng bộ là best-effort, không được làm hỏng luồng chính
        return f"Lỗi không xác định khi đồng bộ: {e}"
