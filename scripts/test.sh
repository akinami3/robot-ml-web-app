#!/usr/bin/env bash
# =============================================================================
# Test Script - Run tests for all or specific services
# テストスクリプト - 全サービスまたは指定サービスのテストを実行
# =============================================================================
#
# 【このスクリプトの目的】
# フロントエンド・バックエンド・ゲートウェイの各テストを実行します。
# ローカル環境（node_modules, .venv, goがある場合）でもDocker経由でも実行可能。
#
# 【使い方】
#   ./scripts/test.sh              # 全サービスのテストを実行
#   ./scripts/test.sh frontend     # フロントエンドのみ
#   ./scripts/test.sh backend      # バックエンドのみ
#   ./scripts/test.sh gateway      # ゲートウェイのみ
#
# 【テストとは？】
# コードが正しく動作するかを自動的に検証する仕組み。
# - ユニットテスト: 関数やクラス単位の小さなテスト
# - 統合テスト: 複数のモジュールを組み合わせたテスト
# - カバレッジ: テストがコード全体の何%をカバーしているかの指標
# =============================================================================

# シェルスクリプトの安全装置
set -euo pipefail

# スクリプトとプロジェクトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# -----------------------------------------------------------------------------
# コマンドライン引数の処理
# -----------------------------------------------------------------------------
# ${1:-all} : 第1引数（$1）のデフォルト値を設定する書き方
#   ${変数:-デフォルト値} : 変数が未定義または空の場合、デフォルト値を使用
#   例: ./test.sh frontend → SERVICE="frontend"
#   例: ./test.sh           → SERVICE="all"（引数なしなのでデフォルト値）
#
# 【Bashの特殊変数】
# $0 : スクリプト自身のファイル名
# $1 : 第1引数、$2 : 第2引数、...
# $# : 引数の個数
# $@ : すべての引数（配列として）
# $? : 直前のコマンドの終了コード
# -----------------------------------------------------------------------------
SERVICE="${1:-all}"

# =============================================================================
# フロントエンドテスト関数
# =============================================================================
# 【関数の定義方法】
# 関数名() { ... } で定義し、関数名 で呼び出す
# シェルスクリプトの関数は、定義した後でないと呼び出せない
#
# 【Vitestとは？】
# Vite（ヴィート）ベースの高速テストフレームワーク。
# React/Vue/TypeScriptのテストに使われる。Jestの代替として人気。
#
# 【テストカバレッジとは？】
# テストがソースコードの何%を実行したかの指標。
# --coverage オプションで計測し、レポートを出力する。
# 例: 80%カバレッジ = コードの80%がテストで実行された
# =============================================================================
run_frontend_tests() {
    echo "=== Frontend Tests ==="
    cd "$PROJECT_DIR/frontend"
    # node_modules/.package-lock.json の存在で、ローカルにnpm installされているか判定
    # node_modules : npmパッケージのインストール先ディレクトリ
    if [ -f node_modules/.package-lock.json ]; then
        # ローカル環境でテスト実行
        # npx : node_modulesにインストールされたコマンドを実行するツール
        # vitest run : テストを1回実行（watchモードではなく）
        # --coverage : コードカバレッジを計測
        npx vitest run --coverage
    else
        # Docker内でテスト実行
        # docker compose exec : 実行中のコンテナ内でコマンドを実行
        # frontend : docker-compose.ymlで定義されたサービス名
        # -- : npmの引数とdocker composeの引数を区別するセパレーター
        docker compose exec frontend npm run test -- --coverage
    fi
    echo "✓ Frontend tests passed"
}

# =============================================================================
# バックエンドテスト関数
# =============================================================================
# 【pytestとは？】
# Pythonの最も人気のあるテストフレームワーク。
# テスト関数は test_ で始まる名前にすると自動で検出される。
#
# 【テストカバレッジオプションの解説】
# --cov=app : appディレクトリのカバレッジを計測
# --cov-report=html : HTML形式のカバレッジレポートを生成
#   → ブラウザで開くと、どの行がテストされたか色分けで確認できる
# --cov-report=term-missing : ターミナルにカバレッジを表示
#   → テストされていない行番号を表示
# -v : verbose（詳細表示）。各テストケースの結果を個別に表示
#
# 【.venv（仮想環境）とは？】
# Pythonのパッケージを、プロジェクトごとに分離して管理する仕組み。
# source .venv/bin/activate : 仮想環境を有効化（そのターミナルのみ）
# deactivate : 仮想環境を無効化（この関数では明示的には呼ばない）
# =============================================================================
run_backend_tests() {
    echo "=== Backend Tests ==="
    cd "$PROJECT_DIR/backend"
    # -d .venv : .venvディレクトリが存在するかチェック
    if [ -d .venv ]; then
        # ローカル環境でテスト実行
        # source : 別のスクリプトを現在のシェルで実行（変数や設定を引き継ぐ）
        #   . (ドット)でも同じ意味: . .venv/bin/activate
        source .venv/bin/activate
        pytest --cov=app --cov-report=html --cov-report=term-missing -v
    else
        # Docker内でテスト実行
        docker compose exec backend pytest --cov=app --cov-report=term-missing -v
    fi
    echo "✓ Backend tests passed"
}

# =============================================================================
# ゲートウェイテスト関数
# =============================================================================
# 【Go言語のテスト】
# go test : Go標準のテストコマンド。_test.goファイルを自動検出
# ./... : カレントディレクトリ以下の全パッケージを対象
#   . : カレントディレクトリ
#   /... : 再帰的にサブディレクトリを含む
# -v : verbose（各テスト関数の結果を個別表示）
# -race : レースコンディション検出器を有効化
#   複数のゴルーチン（Go版のスレッド）が同じデータに同時アクセスするバグを検出
# -coverprofile=coverage.out : カバレッジデータをファイルに出力
#
# go tool cover -func=coverage.out : 関数ごとのカバレッジを表示
#   各関数が何%テストされているかを一覧表示
# =============================================================================
run_gateway_tests() {
    echo "=== Gateway Tests ==="
    cd "$PROJECT_DIR/gateway"
    # command -v go : goコマンドがインストールされているかチェック
    if command -v go &> /dev/null; then
        # ローカル環境でテスト実行
        go test ./... -v -race -coverprofile=coverage.out
        go tool cover -func=coverage.out
    else
        # Docker内でテスト実行（カバレッジファイル出力はなし）
        docker compose exec gateway go test ./... -v -race
    fi
    echo "✓ Gateway tests passed"
}

# =============================================================================
# case文によるサービス選択
# =============================================================================
# case "$SERVICE" in ... esac : 値による条件分岐（switch文に相当）
#
# 【case文の構文】
# case 変数 in
#   パターン1)
#     処理
#     ;;        ← breakに相当。次のパターンに落ちない
#   パターン2)
#     処理
#     ;;
#   *)          ← default（どのパターンにもマッチしない場合）
#     処理
#     ;;
# esac          ← caseの逆綴り。case文の終了
#
# 【if文 vs case文】
# if文: 複雑な条件判定に向いている（ファイル存在チェック、数値比較など）
# case文: 値のパターンマッチングに向いている（文字列の一致判定）
# =============================================================================
case "$SERVICE" in
    frontend)
        run_frontend_tests
        ;;
    backend)
        run_backend_tests
        ;;
    gateway)
        run_gateway_tests
        ;;
    all)
        # 全サービスのテストを順番に実行
        run_frontend_tests
        echo ""
        run_backend_tests
        echo ""
        run_gateway_tests
        echo ""
        echo "=== All Tests Passed ==="
        ;;
    *)
        # どのパターンにもマッチしない場合（不正な引数）
        # $0 : このスクリプト自身のパス（使い方を表示するときの慣例）
        echo "Usage: $0 [frontend|backend|gateway|all]"
        exit 1
        ;;
esac
