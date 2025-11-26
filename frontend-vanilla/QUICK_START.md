# Quick Start Guide - Vanilla JS Version

## 🚀 3ステップで起動

### ステップ 1: バックエンドを起動
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### ステップ 2: フロントエンドを起動
```bash
cd frontend-vanilla
./serve.sh
```
または
```bash
python3 -m http.server 3000
```

### ステップ 3: ブラウザで開く
http://localhost:3000

---

## 📝 基本的な使い方

### ロボット制御
1. 「ロボット制御」タブをクリック
2. ジョイスティックをドラッグしてロボットを操作
3. ナビゲーションパネルで目標位置を設定

### データ記録
1. 「データベース」タブをクリック
2. 記録したいデータ種別を選択
3. 「開始」ボタンをクリック
4. 「保存」または「破棄」で終了

### 機械学習
1. 「機械学習」タブをクリック
2. トレーニング設定を調整
3. 「トレーニング開始」をクリック
4. リアルタイムでグラフを確認

### チャットボット
1. 「チャットボット」タブをクリック
2. メッセージを入力して送信
3. AIからの回答を受信

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 問題: ページが真っ白
**解決策:**
1. ブラウザコンソール（F12）を開いてエラーを確認
2. `js/config.js` のURLが正しいか確認
3. サーバーが正しく起動しているか確認

#### 問題: MQTT/WS接続が失敗
**解決策:**
1. バックエンドが起動しているか確認
2. ヘッダーの接続ステータスインジケーターを確認
3. バックエンドのログを確認

#### 問題: ジョイスティックが動作しない
**解決策:**
1. nipplejs が正しく読み込まれているか確認（ブラウザコンソール）
2. インターネット接続を確認（CDNから読み込み）
3. ページをリロード

---

## 📚 ファイル構造の理解

```
frontend-vanilla/
├── index.html          # エントリーポイント
├── css/
│   ├── main.css       # 基本スタイル
│   └── components.css # コンポーネントスタイル
└── js/
    ├── app.js         # アプリ初期化
    ├── config.js      # 設定（URLなど）
    ├── router.js      # ルーティング
    ├── services/      # API, WebSocketサービス
    ├── store/         # 状態管理
    └── views/         # 各ページのビュー
```

---

## 🎨 カスタマイズ

### APIのURLを変更
`js/config.js` を編集：
```javascript
export const config = {
    apiUrl: 'http://your-server:8000',
    wsUrl: 'ws://your-server:8000',
};
```

### スタイルを変更
`css/main.css` のカスタムプロパティを編集：
```css
:root {
    --primary-color: #2563eb;  /* メインカラー */
    --danger-color: #ef4444;   /* エラーカラー */
    /* ... */
}
```

### 新しいビューを追加
1. `js/views/` に新しいファイルを作成
2. `EXAMPLE_VIEW.js` を参考に実装
3. `js/app.js` でルートを登録
4. `index.html` にナビゲーションリンクを追加

---

## 💡 開発のヒント

### デバッグ
- ブラウザ DevTools（F12）を開いて使用
- Console タブでログを確認
- Network タブでAPI呼び出しを確認
- Elements タブでDOMを検査

### パフォーマンス
- 不要なDOM更新を避ける
- WebSocket接続を適切にクリーンアップ
- イベントリスナーを削除

### ベストプラクティス
- `cleanup()` メソッドを実装してリソースを解放
- エラーハンドリングを適切に実装
- console.log を使ってデバッグ情報を出力

---

## 🌐 ブラウザ対応

対応ブラウザ:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

必要な機能:
- ES6 Modules
- WebSocket
- Fetch API
- CSS Grid & Flexbox

---

## 📞 サポート

問題が解決しない場合:
1. `README.md` を確認
2. `COMPARISON.md` で実装の詳細を確認
3. `SETUP.html` をブラウザで開いてガイドを確認
4. ブラウザコンソールのエラーメッセージを確認

---

**準備完了！ 楽しい開発を！ 🎉**
