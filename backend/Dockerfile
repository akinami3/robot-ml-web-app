# =============================================================================
# バックエンド用 Dockerfile（本番環境向け）
# =============================================================================
#
# 【概要】
# Python（FastAPI）バックエンドサーバーのDockerイメージを構築します。
# マルチステージビルドにより、ビルドツールを含まない軽量な本番イメージを生成します。
#
# 【マルチステージビルドの流れ】
#   ステージ1（builder）: 依存関係をインストール（pip, setuptools等のツール含む）
#   ステージ2（runtime）: ステージ1の成果物だけをコピーして実行環境を構築
#   結果: pip, setuptools, wheel 等のビルドツールが最終イメージに含まれない
# =============================================================================

# ─── ビルドステージ（Build Stage）────────────────────────────────
# 【python:3.12-slim】Python 3.12 の Debian slim版
#   - slim: 通常のDebianイメージから不要なパッケージを除いた軽量版
#     通常版 ~900MB → slim版 ~150MB
#   - Alpine版もあるが、Pythonとの相性の問題で slim が推奨されることが多い
#     （Alpine は musl libc を使うため、一部のPythonパッケージでの
#      コンパイルが遅い/失敗することがある）
# 【AS builder】このステージに「builder」という名前をつける
FROM python:3.12-slim AS builder

# 作業ディレクトリを /app に設定
WORKDIR /app

# 【pip関連ツールのアップグレード】
# --no-cache-dir: ダウンロードしたパッケージのキャッシュを保存しない
#   → イメージサイズを削減
# --upgrade: 最新バージョンにアップグレード
# pip: Pythonのパッケージマネージャー
# setuptools: Pythonパッケージのビルドに必要なツール
# wheel: コンパイル済みパッケージ形式（インストールが高速になる）
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 【pyproject.toml】Pythonプロジェクトの設定ファイル
# 依存関係（必要なライブラリ一覧）やプロジェクト情報が記載されている
# 従来の setup.py + requirements.txt を統合した新しい標準形式
COPY pyproject.toml .

# アプリケーションコードをコピー
COPY app/ ./app/

# 【依存関係のインストール】
# --prefix=/install: /install ディレクトリにインストール
#   → 後のステージでこのディレクトリだけコピーすれば、依存関係を持ってこれる
# . : カレントディレクトリの pyproject.toml を使ってインストール
RUN pip install --no-cache-dir --prefix=/install .

# ─── ランタイムステージ（Runtime Stage）──────────────────────────
# 実際にアプリケーションを実行する軽量なイメージ
FROM python:3.12-slim AS runtime

# 【非rootユーザーの作成】セキュリティのベストプラクティス
# コンテナ内でrootユーザーとして実行すると、コンテナが侵害された場合に
# ホストシステムへの影響が大きくなる（コンテナエスケープ攻撃）
#
# groupadd -r appuser: 「appuser」というシステムグループを作成
#   -r: システムグループ（通常のユーザー用ではなくサービス用）
# useradd -r -g appuser appuser: 「appuser」というシステムユーザーを作成
#   -r: システムユーザー, -g appuser: appuserグループに所属
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 作業ディレクトリの設定
WORKDIR /app

# 【ビルドステージからの成果物コピー】
# --from=builder: builderステージからコピー
# /install の中身を /usr/local にコピー
# → ビルドステージでインストールしたPythonパッケージが使えるようになる
COPY --from=builder /install /usr/local

# アプリケーションコード全体をコピー
COPY . .

# 【必要なディレクトリの作成と権限設定】
# /app/keys: JWT認証の鍵ファイルを保存するディレクトリ
# /tmp/exports: データエクスポート用の一時ディレクトリ
# chown -R appuser:appuser: ディレクトリの所有者をappuserに変更
#   -R: サブディレクトリも含めて再帰的に変更
# → appuserがファイルの読み書きをできるようにする
RUN mkdir -p /app/keys /tmp/exports && \
    chown -R appuser:appuser /app /tmp/exports

# 【USER】以降のコマンドを appuser として実行（rootではなく）
# セキュリティ上、必要最低限の権限でアプリを実行します
USER appuser

# 【EXPOSE 8000】FastAPIサーバーがリッスンするポート番号を文書化
EXPOSE 8000

# 【HEALTHCHECK】コンテナの健康状態を定期的に確認
#   --interval=30s    : 30秒ごとにチェック
#   --timeout=10s     : 10秒以内に応答がなければ失敗（バックエンドは処理が重い場合がある）
#   --start-period=10s : 起動後10秒間は失敗してもOK（初期化時間を考慮）
#   --retries=3       : 3回連続失敗で異常判定
#
# Python でHTTPリクエストを送信し、/health エンドポイントの応答を確認
# httpx: Pythonの高機能HTTPクライアントライブラリ
# raise_for_status(): HTTPエラー（4xx, 5xx）の場合に例外を発生させる
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()" || exit 1

# 【CMD】コンテナ起動時に実行するコマンド
# uvicorn: ASGIサーバー（非同期Pythonウェブアプリケーションを実行するサーバー）
#   app.main:app → app/main.py 内の app オブジェクト（FastAPIインスタンス）を起動
#   --host 0.0.0.0 → すべてのネットワークインターフェースでリッスン
#   --port 8000    → ポート8000で待ち受け
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
