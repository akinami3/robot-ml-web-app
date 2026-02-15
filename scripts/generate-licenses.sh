#!/usr/bin/env bash
# =============================================================================
# OSS License Generation Script
# オープンソースライセンス レポート生成スクリプト
# =============================================================================
#
# 【このスクリプトの目的】
# プロジェクトで使用している全てのオープンソースライブラリのライセンス情報を
# 収集し、レポートファイルとして出力します。
#
# 【なぜライセンススキャンが重要なの？】
# オープンソースソフトウェア（OSS）は「無料」ですが「自由に使える」わけではありません。
# 各ライブラリにはライセンス条件があり、それを守る必要があります:
#
#   MIT License:
#     - 最も緩い。著作権表示を含めればほぼ何でもOK
#     - 商用利用OK、改変OK、再配布OK
#
#   Apache License 2.0:
#     - MITに近いが、特許権の付与条項がある
#     - 変更した場合は変更したことの明記が必要
#
#   GPL (GNU General Public License):
#     - コピーレフト型。GPLコードを使ったソフトもGPLにする必要がある
#     - 商用ソフトに組み込む場合は注意が必要
#     - LGPL: ライブラリとしてリンクする分にはGPL化不要（緩い版）
#
#   BSD License:
#     - MITに近い。著作権表示と免責条項の記載が必要
#
# 【ライセンスコンプライアンス（法令遵守）】
# ソフトウェアを配布・公開する際は:
#   1. 使用しているOSSのライセンスを全て確認
#   2. 各ライセンスの条件を満たす（著作権表示など）
#   3. ライセンスの互換性を確認（GPL + MIT は可能だが逆は不可の場合も）
# このスクリプトでライセンス一覧を自動生成し、確認を容易にします。
#
# 【使い方】
#   ./scripts/generate-licenses.sh
# =============================================================================

# シェルスクリプトの安全装置
set -euo pipefail

# ディレクトリパスの設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# ライセンスレポートの出力先（ドキュメントのlegalディレクトリ）
OUTPUT_DIR="$PROJECT_DIR/docs/docs/legal"

# 出力ディレクトリを作成
mkdir -p "$OUTPUT_DIR"

echo "=== Generating OSS License Reports ==="

# =============================================================================
# フロントエンド（npm）のライセンススキャン
# =============================================================================
# 【npm（Node Package Manager）のライセンスツール】
# license-checker : npmパッケージのライセンス情報を抽出するツール
#   --json : JSON形式で出力（プログラムで処理しやすい）
#   --csv  : CSV形式で出力（Excelで開ける）
#   --out  : 出力先ファイルパス
#
# 【node_modulesとは？】
# npm install でインストールされたパッケージの保存先。
# 1つのプロジェクトで数百〜数千のパッケージが依存関係として入ることもある。
# 全てのライセンスを手動で確認するのは現実的ではないので、ツールを使う。
# =============================================================================
echo "Scanning frontend dependencies..."
cd "$PROJECT_DIR/frontend"
# ローカルにnpm installされているか確認
if [ -f node_modules/.package-lock.json ]; then
    # npx : npmパッケージのコマンドを実行するツール
    # 2>/dev/null : エラー出力を抑制
    # || true : 失敗してもスクリプトを続行（一部パッケージの情報が取れなくてもOK）
    npx license-checker --json --out "$OUTPUT_DIR/frontend-licenses.json" 2>/dev/null || true
    npx license-checker --csv --out "$OUTPUT_DIR/frontend-licenses.csv" 2>/dev/null || true
    echo "✓ Frontend licenses generated"
else
    # ⚠ : 警告マーク。エラーではないが注意が必要
    echo "⚠ Frontend node_modules not found. Run 'npm install' first."
fi

# =============================================================================
# バックエンド（pip）のライセンススキャン
# =============================================================================
# 【pip-licenses とは？】
# Pythonパッケージのライセンス情報を一覧表示するツール。
# pip install pip-licenses でインストールできる。
#   --format=json : JSON形式で出力
#   --format=csv  : CSV形式で出力
#   --output-file : 出力先ファイル
#
# 【Pythonの仮想環境（venv）】
# .venv : Python仮想環境のディレクトリ
# source .venv/bin/activate : 仮想環境を有効化
#   → pip installしたパッケージがこの仮想環境に閉じ込められる
# deactivate : 仮想環境を無効化（元のPython環境に戻る）
# =============================================================================
echo "Scanning backend dependencies..."
cd "$PROJECT_DIR/backend"
if [ -d .venv ]; then
    # 仮想環境を有効化
    source .venv/bin/activate
    pip-licenses --format=json --output-file="$OUTPUT_DIR/backend-licenses.json" 2>/dev/null || true
    pip-licenses --format=csv --output-file="$OUTPUT_DIR/backend-licenses.csv" 2>/dev/null || true
    # 仮想環境を無効化
    deactivate
    echo "✓ Backend licenses generated"
else
    echo "⚠ Backend venv not found. Run 'python -m venv .venv && pip install -e .[dev]' first."
fi

# =============================================================================
# ゲートウェイ（Go）のライセンススキャン
# =============================================================================
# 【go-licenses とは？】
# Googleが開発したGoモジュールのライセンス情報収集ツール。
# インストール: go install github.com/google/go-licenses@latest
#
# go-licenses csv ./... : カレントディレクトリ以下の全パッケージのライセンスをCSV出力
#   ./... : Go特有の記法で「このディレクトリ以下の全パッケージ」を意味
#
# 【Go Modules】
# Go言語のパッケージ管理システム。
# go.mod : プロジェクトの依存関係を定義するファイル
# go.sum : 依存パッケージのチェックサム（改ざん検知用）
# =============================================================================
echo "Scanning gateway dependencies..."
cd "$PROJECT_DIR/gateway"
# go-licensesコマンドが利用可能かチェック
if command -v go-licenses &> /dev/null; then
    go-licenses csv ./... > "$OUTPUT_DIR/gateway-licenses.csv" 2>/dev/null || true
    echo "✓ Gateway licenses generated"
else
    echo "⚠ go-licenses not found. Install: go install github.com/google/go-licenses@latest"
fi

echo ""
echo "=== License reports generated in $OUTPUT_DIR ==="
