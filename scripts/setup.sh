#!/usr/bin/env bash
# =============================================================================
# Setup Script - Initial environment setup
# セットアップスクリプト - 初期環境構築
# =============================================================================
#
# 【このスクリプトの目的】
# プロジェクトを初めてクローンした後に1回だけ実行します。
# 以下の初期設定を自動で行います:
#   1. Docker / Docker Compose のインストール確認
#   2. .envファイル（環境変数設定）の作成
#   3. JWT認証用のRSA鍵ペアの生成
#   4. データ保存用ディレクトリの作成
#
# 【使い方】
#   ./scripts/setup.sh
#
# 通常はdev.shから自動的に呼ばれるので、手動で実行する必要はありません。
# =============================================================================

# シェルスクリプトの安全装置（詳細はdev.shを参照）
# set -e : エラー時に即停止
# set -u : 未定義変数の使用をエラーにする
# set -o pipefail : パイプラインのエラーを検出
set -euo pipefail

# スクリプトのディレクトリとプロジェクトルートを取得
# （BASH_SOURCE、dirname、cdの詳細はdev.shを参照）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Robot AI Web Application - Setup ==="
echo ""

# =============================================================================
# Dockerのインストールチェック
# =============================================================================
# command -v <コマンド名> : コマンドがインストールされているか確認
#   インストールされている場合 → コマンドのパスを返す（例: /usr/bin/docker）
#   インストールされていない場合 → 何も返さず、終了コード1
#
# &> /dev/null : 標準出力とエラー出力を両方とも /dev/null に捨てる
#   /dev/null : Linux/Unixの「ブラックホール」デバイス。書き込んだデータは消える
#   &> : 標準出力（1）もエラー出力（2）もまとめてリダイレクト
#
# ! : 否定。コマンドが失敗した場合（＝Dockerがない場合）にif文の中に入る
#
# 【Dockerとは？】
# アプリケーションを「コンテナ」という隔離された環境で実行するツール。
# 開発者全員が同じ環境で開発できるので「自分のPCでは動くのに...」が起きない。
# Docker >= 24.0 : バージョン24.0以上が必要
# =============================================================================
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker >= 24.0"
    exit 1
    # exit 1 : スクリプトをエラー終了（終了コード1 = 異常終了）
    # exit 0 なら正常終了を意味する
fi

# Docker Composeのインストールチェック
# docker compose : Docker Compose V2（dockerのサブコマンドとして統合されたバージョン）
# 旧バージョンは docker-compose（ハイフン付き）だったが、現在は非推奨
if ! command -v docker compose &> /dev/null; then
    echo "ERROR: Docker Compose is not available. Please install Docker Compose >= 2.20"
    exit 1
fi

# -----------------------------------------------------------------------------
# バージョン情報の表示
# -----------------------------------------------------------------------------
# docker --version : Dockerのバージョンを表示
# grep -oP '\d+\.\d+\.\d+' : バージョン番号だけを正規表現で抽出
#   -o : マッチした部分だけ出力
#   -P : Perl互換の正規表現を使用
#   \d+ : 1桁以上の数字  \. : ドット
#   例: "Docker version 24.0.7, build afdd53b" → "24.0.7"
#
# ✓ : チェックマーク。成功したことを視覚的に示す
echo "✓ Docker $(docker --version | grep -oP '\d+\.\d+\.\d+')"
echo "✓ Docker Compose $(docker compose version --short)"

# =============================================================================
# .envファイルの作成
# =============================================================================
# 【.envファイルとは？】
# 環境変数を定義するファイル。以下のような機密情報や設定値を保存:
#   - データベースのパスワード
#   - APIキー
#   - サーバーのポート番号
#   - デバッグモードのON/OFF
#
# 【なぜ.env.exampleから.envにコピーするの？】
# .env.example : テンプレート。Gitで共有される（パスワードはダミー値）
# .env         : 実際の設定。Gitには含めない（.gitignoreで除外）
# → こうすることで、パスワードをGitに公開してしまう事故を防げる
#
# [ ! -f "$PROJECT_DIR/.env" ] : .envファイルが存在しない場合
# =============================================================================
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo ""
    echo "Creating .env from .env.example..."
    # cp : ファイルコピーコマンド（copy）
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo "✓ .env created. Please review and update passwords."
else
    echo "✓ .env already exists"
fi

# =============================================================================
# JWT認証用のRSA鍵ペア生成
# =============================================================================
# 【JWTとは？】
# JSON Web Token（ジェーソン・ウェブ・トークン）
# ユーザーのログイン状態を安全に管理するための仕組み。
# ログイン成功時にサーバーが「トークン」を発行し、
# 以降のリクエストでそのトークンを送ることで本人確認する。
#
# 【RSA鍵とは？】
# 公開鍵暗号方式の一種。2つの鍵（ペア）を使う:
#   - 秘密鍵（private.pem）: トークンに署名する（サーバーだけが持つ）
#   - 公開鍵（public.pem） : 署名を検証する（誰でも持てる）
# → 秘密鍵で署名されたトークンは、公開鍵で「本物かどうか」確認できる
#
# 【なぜRSA？（対称鍵 vs 非対称鍵）】
# 対称鍵（HS256）: 1つの鍵で署名と検証の両方を行う → シンプルだが鍵の共有が危険
# 非対称鍵（RS256）: 署名と検証で別の鍵 → 安全。マイクロサービスに最適
# (e.g., ゲートウェイは公開鍵だけ持てばトークンを検証できる)
#
# [ ! -d "$PROJECT_DIR/keys" ] : keysディレクトリが存在しない場合
#   -d : ディレクトリが存在するか確認（-fはファイル、-dはディレクトリ）
# =============================================================================
if [ ! -d "$PROJECT_DIR/keys" ]; then
    echo ""
    echo "Generating JWT RSA keys..."
    # mkdir -p : ディレクトリを作成。-pは親ディレクトリも自動作成
    mkdir -p "$PROJECT_DIR/keys"

    # openssl genrsa : RSA秘密鍵を生成するコマンド
    #   -out : 出力先ファイルパス
    #   2048 : 鍵の長さ（ビット数）。2048ビットは現在の推奨最小値
    #          数字が大きいほど安全だが、処理が遅くなる
    #   2>/dev/null : エラー出力を抑制（進捗表示を非表示にする）
    openssl genrsa -out "$PROJECT_DIR/keys/private.pem" 2048 2>/dev/null

    # openssl rsa -pubout : 秘密鍵から公開鍵を抽出する
    #   -in : 入力ファイル（秘密鍵）
    #   -pubout : 公開鍵として出力
    openssl rsa -in "$PROJECT_DIR/keys/private.pem" -pubout -out "$PROJECT_DIR/keys/public.pem" 2>/dev/null

    # chmod : ファイルのアクセス権限を設定するコマンド
    # 【Linuxのファイル権限（パーミッション）】
    # 3桁の数字で指定: [所有者][グループ][その他]
    # 各桁は以下の合計:
    #   4 = 読み取り（Read）
    #   2 = 書き込み（Write）
    #   1 = 実行（Execute）
    #
    # chmod 600 : 所有者のみ読み書き可能（6=4+2）、他は一切不可（0）
    #   → 秘密鍵は絶対に他人に読まれてはいけないため、厳しい制限
    chmod 600 "$PROJECT_DIR/keys/private.pem"

    # chmod 644 : 所有者は読み書き可能、他は読み取りのみ
    #   → 公開鍵は名前の通り「公開」してOKなので、読み取りは許可
    chmod 644 "$PROJECT_DIR/keys/public.pem"

    echo "✓ RSA keys generated in keys/"
else
    echo "✓ JWT RSA keys already exist"
fi

# =============================================================================
# データ用ディレクトリの作成
# =============================================================================
# 【各ディレクトリの用途】
# data/datasets : 機械学習用のデータセット（訓練データ、テストデータ）
# data/models   : 学習済みモデルファイル（.pth, .h5, .onnx等）
# data/logs     : アプリケーションのログファイル
# data/images   : ロボットのカメラ画像、地図画像など
# uploads/ml    : ユーザーがアップロードしたMLファイル
# backups       : データベースのバックアップファイル
#
# mkdir -p : -p（parents）オプションで、途中のディレクトリも自動作成
#   例: mkdir -p data/datasets → dataディレクトリがなければ先に作成
# =============================================================================
echo ""
echo "Creating data directories..."
mkdir -p "$PROJECT_DIR/data/datasets"
mkdir -p "$PROJECT_DIR/data/models"
mkdir -p "$PROJECT_DIR/data/logs"
mkdir -p "$PROJECT_DIR/data/images"
mkdir -p "$PROJECT_DIR/uploads/ml"
mkdir -p "$PROJECT_DIR/backups"
echo "✓ Data directories created"

# =============================================================================
# セットアップ完了メッセージ
# =============================================================================
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Review and update .env (especially passwords)"
# ↑ .envファイルのパスワードをデフォルト値から変更してください
echo "  2. Start services: ./scripts/dev.sh"
# ↑ 開発サーバーを起動するコマンド
echo "  3. Pull LLM model: docker compose exec ollama ollama pull llama3"
# ↑ OllamaでLLMモデル（llama3）をダウンロード
#   Ollama : ローカルでLLM（大規模言語モデル）を実行するツール
#   llama3 : Metaが開発したオープンソースのLLM
echo ""
