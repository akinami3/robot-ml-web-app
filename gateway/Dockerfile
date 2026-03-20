# =============================================================================
# Step 3: Gateway Dockerfile
# =============================================================================
#
# 【マルチステージビルド（Multi-stage Build）】
# 2つの段階に分けてイメージを作る:
#   1. builder: Go のコンパイル（開発ツールが入った大きなイメージ）
#   2. runner: 実行（最小限のイメージ）
#
# なぜ分ける？
# Go のコンパイラは数百MBあるが、実行するのは1つのバイナリだけ。
# 最終イメージにコンパイラを含めると無駄に大きくなる。
#
# builder: ~800MB → runner: ~15MB（約50分の1）
#
# =============================================================================

# --- Stage 1: ビルド ---
FROM golang:1.22-alpine AS builder

WORKDIR /app

# 依存関係を先にダウンロード（キャッシュ活用）
# go.mod / go.sum が変わらなければ、この層はキャッシュされる。
COPY go.mod go.sum ./
RUN go mod download

# ソースコードをコピーしてビルド
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o gateway ./cmd/gateway

# --- Stage 2: 実行 ---
# alpine: 軽量 Linux ディストリビューション（約5MB）
FROM alpine:3.19

WORKDIR /app

# ビルドしたバイナリをコピー
COPY --from=builder /app/gateway .

# ヘルスチェック用のツール
RUN apk add --no-cache wget

EXPOSE 8080

# 実行
CMD ["./gateway"]
