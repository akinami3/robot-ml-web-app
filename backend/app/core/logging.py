"""Logging configuration using structlog."""

# =============================================================================
# 構造化ログ（Structured Logging）の設定モジュール
# =============================================================================
#
# 【構造化ログとは？】
#   通常のログは「テキストの1行」として出力されます（例: "Error occurred"）。
#   構造化ログでは、ログをJSON形式で出力します。
#   例: {"event": "Error occurred", "user_id": 123, "timestamp": "2026-01-01T00:00:00"}
#
#   JSON形式にすることで、ログの検索・フィルタリング・分析が格段に楽になります。
#   本番環境ではElasticsearchやDatadogなどのツールでログを自動解析するため、
#   JSON形式は事実上の標準になっています。
#
# 【structlogとは？】
#   Pythonの標準loggingモジュールをラップし、構造化ログを簡単に実現するライブラリです。
#   「プロセッサ（processor）」をチェーン（連鎖）させてログを加工するのが特徴です。
#   各プロセッサがログにタイムスタンプを追加したり、レベルを付けたりします。
# =============================================================================

import logging
import sys

import structlog


def setup_logging(level: str = "info") -> None:
    """Configure structured logging."""

    # --- ログレベルの設定 ---
    # level引数（例: "info", "debug", "warning"）を、Pythonのloggingモジュールの
    # 定数（logging.INFO = 20, logging.DEBUG = 10 など）に変換します。
    # getattr(logging, "INFO") → logging.INFO (= 20) を返します。
    # 無効な文字列が渡された場合、デフォルトとしてlogging.INFOを使います。
    log_level = getattr(logging, level.upper(), logging.INFO)

    # --- structlogの設定 ---
    # structlog.configure() で、ログがどのように処理されるかを一括設定します。
    structlog.configure(
        # 【processors（プロセッサ）とは？】
        # ログメッセージが出力される前に、順番に通過する「加工ステップ」のリストです。
        # パイプライン（流れ作業）のように、各ステップがログに情報を追加・変換します。
        processors=[
            # 1. contextvars から追加コンテキストをマージ
            #    → リクエストIDやユーザーIDなど、スレッド/タスク固有の情報を
            #      自動的にログに含めることができます。
            structlog.contextvars.merge_contextvars,

            # 2. ログレベル（info, warning, error など）をログに追加
            structlog.processors.add_log_level,

            # 3. スタックトレース情報をレンダリング
            #    → エラー発生時にどの関数からどの関数が呼ばれたかの情報を表示します。
            structlog.processors.StackInfoRenderer(),

            # 4. 例外情報を自動的に設定
            #    → logger.error() 呼出し時に例外情報を自動キャプチャします。
            structlog.dev.set_exc_info,

            # 5. ISO 8601形式のタイムスタンプを追加
            #    → 例: "2026-02-15T10:30:00Z"（世界共通の日時フォーマット）
            structlog.processors.TimeStamper(fmt="iso"),

            # 6. 最終ステップ：すべての情報をJSON文字列に変換して出力
            #    → {"event": "...", "level": "info", "timestamp": "..."} のような出力になります。
            structlog.processors.JSONRenderer(),
        ],

        # 【wrapper_class】
        # 設定したlog_level以下のログを自動的にフィルタリング（無視）するラッパーです。
        # 例: log_level=INFO なら、debug レベルのログは出力されません。
        wrapper_class=structlog.make_filtering_bound_logger(log_level),

        # 【context_class】
        # ログのコンテキスト（付加情報）を保持するデータ構造。
        # 通常はPythonのdict（辞書）を使います。
        context_class=dict,

        # 【logger_factory】
        # 実際にログを「どこに」出力するかを決めるファクトリです。
        # ここではsys.stdout（標準出力＝ターミナル/コンソール）に出力しています。
        # Docker環境では標準出力に出すのが一般的です（コンテナのログとして収集されるため）。
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),

        # 【cache_logger_on_first_use】
        # True にすると、初回使用時にロガーをキャッシュ（保存）して再利用します。
        # パフォーマンスの最適化です。毎回ロガーを作り直すコストを削減します。
        cache_logger_on_first_use=True,
    )
