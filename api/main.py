"""
シンプルスクレイピング用 HTTP API。

環境変数:
  API_KEY — 設定時はリクエストヘッダ X-API-Key と一致が必要
  API_SCRAPE_ALLOWED_HOST_SUFFIXES — 許可するホスト（カンマ区切り、既定: .2ch.sc,2ch.sc）
  API_SCRAPE_TIMEOUT_SEC — 子プロセスのタイムアウト秒（既定: 180）

起動例（リポジトリルートで）:
  PYTHONPATH=. uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import ipaddress
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent


def _default_allowed_suffixes() -> list[str]:
    raw = os.getenv("API_SCRAPE_ALLOWED_HOST_SUFFIXES", ".2ch.sc,2ch.sc")
    return [x.strip().lower() for x in raw.split(",") if x.strip()]


def _timeout_sec() -> float:
    return float(os.getenv("API_SCRAPE_TIMEOUT_SEC", "180"))


def _verify_api_key(header_value: str | None) -> None:
    expected = os.getenv("API_KEY", "").strip()
    if not expected:
        return
    got = (header_value or "").strip()
    if len(got) != len(expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not secrets.compare_digest(got, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")


def _host_is_ip_literal(host: str) -> bool:
    h = host.strip("[]")
    try:
        ipaddress.ip_address(h)
        return True
    except ValueError:
        return False


def _host_allowed(hostname: str, suffixes: list[str]) -> bool:
    h = hostname.lower()
    for s in suffixes:
        if s.startswith("."):
            if h.endswith(s) or h == s.lstrip("."):
                return True
        else:
            if h == s or h.endswith(f".{s}"):
                return True
    return False


def validate_scrape_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("url が空です")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("http または https の URL のみ許可します")
    host = parsed.hostname
    if not host:
        raise ValueError("ホスト名が取得できません")
    if _host_is_ip_literal(host):
        raise ValueError("IP リテラルのホストは許可しません")
    suffixes = _default_allowed_suffixes()
    if suffixes and not _host_allowed(host, suffixes):
        raise ValueError("このホストへのリクエストは許可されていません")
    return url


class ScrapeRequest(BaseModel):
    url: str = Field(..., min_length=1, description="read.cgi 形式のスレッド URL")


app = FastAPI(title="thread-crawler simple scrape API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scrape")
def scrape_thread(
    body: ScrapeRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
):
    _verify_api_key(x_api_key)
    try:
        target_url = validate_scrape_url(body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    cmd = [sys.executable, "-m", "crawler.scrape_one_for_api", target_url]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=_timeout_sec(),
            cwd=str(REPO_ROOT),
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        raise HTTPException(
            status_code=504,
            detail="Scrape timeout",
        ) from e

    if proc.returncode != 0:
        err_detail = proc.stderr.strip() or proc.stdout.strip() or "scrape failed"
        try:
            err_json = json.loads(err_detail)
            err_detail = err_json.get("error", err_detail)
        except json.JSONDecodeError:
            pass
        raise HTTPException(status_code=502, detail=err_detail)

    try:
        payload = json.loads(proc.stdout.strip())
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=502,
            detail="Invalid JSON from scraper",
        ) from e

    return payload
