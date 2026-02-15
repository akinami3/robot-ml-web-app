#!/usr/bin/env bash
# =============================================================================
# Proto Generation Script
# Protocol Buffer コード生成スクリプト
# =============================================================================
#
# 【このスクリプトの目的】
# .protoファイル（インターフェース定義）から、
# PythonとGoのソースコードを自動生成します。
#
# 【Protocol Buffers（プロトコルバッファ）とは？】
# Googleが開発したデータシリアライズ形式。
# 「シリアライズ」= データを送受信可能なバイト列に変換すること。
#
# 通常のJSON: {"name": "Taro", "age": 20} → 人間には読みやすいが、データ量が多い
# Protocol Buffers: バイナリ形式 → 人間には読めないが、高速で軽量
#
# プロトコルバッファの利点:
#   1. 高速: JSONの3-10倍速い
#   2. 軽量: JSONの1/3-1/10のデータサイズ
#   3. 型安全: .protoファイルで型を厳密に定義
#   4. 多言語対応: .protoから各言語のコードを自動生成
#
# 【gRPC（ジーアールピーシー）とは？】
# Googleが開発した高性能RPC（Remote Procedure Call）フレームワーク。
# RPCとは、ネットワーク越しに別のサーバーの関数を呼び出す仕組み。
# gRPCはProtocol Buffersをメッセージ形式として使う。
#
# 【このプロジェクトでの使い方】
# フロントエンド ←(WebSocket)→ ゲートウェイ(Go) ←(gRPC)→ バックエンド(Python)
# → ゲートウェイとバックエンドの通信にgRPCを使用
# → .protoファイルからPython・Goの両方のコードを生成
#
# 【使い方】
#   ./scripts/generate-proto.sh
# =============================================================================

# シェルスクリプトの安全装置
set -euo pipefail

# ディレクトリパスの設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
# .protoファイルが格納されているディレクトリ
PROTO_DIR="$PROJECT_DIR/proto"

echo "=== Generating Protocol Buffer code ==="

# =============================================================================
# Python（バックエンド）用のコード生成
# =============================================================================
# 【生成されるファイル】
# .protoファイル1つから以下の3つのPythonファイルが生成される:
#   *_pb2.py     : メッセージクラス（データ構造の定義）
#   *_pb2_grpc.py: gRPCサービスのスタブ（クライアント/サーバーのコード）
#   *_pb2.pyi    : 型ヒントファイル（IDEの補完に使用）
#
# 【generatedコードの配置先】
# backend/app/infrastructure/grpc/proto/ に生成される
# → バックエンドのPythonコードからimportして使う
# =============================================================================
PYTHON_OUT="$PROJECT_DIR/backend/app/infrastructure/grpc/proto"
# 出力ディレクトリを作成（-p: 親ディレクトリも含めて作成）
mkdir -p "$PYTHON_OUT"
# __init__.py : Pythonのパッケージを示す空ファイル
# touchコマンド: ファイルが存在しなければ作成、存在すれば更新日時を更新
touch "$PYTHON_OUT/__init__.py"

echo "Generating Python code..."
# python -m grpc_tools.protoc : Pythonのprotocコンパイラを実行
#   -m : Pythonモジュールとして実行
#   grpc_tools.protoc : grpcioパッケージに含まれるprotocコンパイラ
#
# -I "$PROTO_DIR" : インクルードパス（importの検索先ディレクトリ）
#   -I : Include path の略
#   .protoファイル内の import "sensor.proto" を解決するために必要
#
# --python_out : メッセージクラス（*_pb2.py）の出力先
# --grpc_python_out : gRPCサービスコード（*_pb2_grpc.py）の出力先
# --pyi_out : 型ヒントファイル（*_pb2.pyi）の出力先
#
# "$PROTO_DIR"/*.proto : protoディレクトリ内の全.protoファイルを対象
#   * (ワイルドカード) : 任意のファイル名にマッチ
python -m grpc_tools.protoc \
    -I "$PROTO_DIR" \
    --python_out="$PYTHON_OUT" \
    --grpc_python_out="$PYTHON_OUT" \
    --pyi_out="$PYTHON_OUT" \
    "$PROTO_DIR"/*.proto

echo "✓ Python proto files generated in $PYTHON_OUT"

# =============================================================================
# Go（ゲートウェイ）用のコード生成
# =============================================================================
# 【生成されるファイル】
# .protoファイル1つから以下の2つのGoファイルが生成される:
#   *.pb.go      : メッセージの構造体（struct）定義
#   *_grpc.pb.go : gRPCサービスのインターフェースと実装
#
# 【protoc vs python -m grpc_tools.protoc】
# Python : grpc_toolsパッケージに含まれるprotocを使用
# Go     : システムにインストールされたprotocコマンドを使用
#          + protoc-gen-go / protoc-gen-go-grpc プラグインが必要
# =============================================================================
GO_OUT="$PROJECT_DIR/gateway/internal/bridge/proto"
mkdir -p "$GO_OUT"

echo "Generating Go code..."
# protoc : Protocol Buffersのコンパイラ（公式ツール）
#
# --go_out : Goのメッセージコードの出力先
# --go_opt=paths=source_relative : 出力パスを.protoファイルから相対的に決定
#   source_relative: .protoファイルと同じディレクトリ構造で出力
# --go-grpc_out : GoのgRPCサービスコードの出力先
# --go-grpc_opt=paths=source_relative : 同上
protoc \
    -I "$PROTO_DIR" \
    --go_out="$GO_OUT" --go_opt=paths=source_relative \
    --go-grpc_out="$GO_OUT" --go-grpc_opt=paths=source_relative \
    "$PROTO_DIR"/*.proto

echo "✓ Go proto files generated in $GO_OUT"
echo ""
echo "=== Proto generation complete ==="
