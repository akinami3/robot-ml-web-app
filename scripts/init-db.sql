-- =============================================================================
-- Step 7: PostgreSQL 初期化スクリプト
-- =============================================================================
--
-- 【このファイルの役割】
-- Docker Compose で PostgreSQL コンテナが初回起動するときに実行される。
-- /docker-entrypoint-initdb.d/ にマウントすることで自動実行。
--
-- 【なぜ必要？】
-- PostgreSQL コンテナのデフォルトでは、
-- POSTGRES_DB で指定したデータベースが1つ作成される。
-- 追加のデータベースやユーザーが必要な場合はこのスクリプトで作成する。
--
-- Step 7 では docker-compose.yml の POSTGRES_DB=robotdb で十分だが、
-- 学習のために SQL でのデータベース/ユーザー作成方法を示す。
--
-- =============================================================================

-- 注意: docker-compose の POSTGRES_DB 環境変数で robotdb は自動作成されるため、
-- ここでは追加のセットアップのみ行う。

-- テスト用データベースの作成（テスト時に使用）
-- CREATE DATABASE robotdb_test;

-- 拡張機能の有効化（UUID 生成に必要）
-- PostgreSQL 13+ ではデフォルトで使用可能だが、明示的に有効化
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- 初期データの投入（サンプルロボット）
-- =============================================================================
--
-- 【INSERT 文の構文】
-- INSERT INTO テーブル名 (カラム1, カラム2, ...) VALUES (値1, 値2, ...);
--
-- uuid_generate_v4() は uuid-ossp 拡張が提供する UUID 生成関数。
-- NOW() は現在のタイムスタンプ。
--
INSERT INTO robots (id, name, robot_type, description, status, created_at, updated_at)
VALUES
    (uuid_generate_v4(), 'TurtleBot3', 'differential', '教育・研究用差動二輪ロボット。ROS2 対応。', 'offline', NOW(), NOW()),
    (uuid_generate_v4(), 'Scout Mini', 'differential', '屋外対応の小型自律移動ロボット。', 'offline', NOW(), NOW()),
    (uuid_generate_v4(), 'MecanumBot', 'omni', 'メカナムホイール搭載の全方向ロボット。', 'offline', NOW(), NOW())
ON CONFLICT (name) DO NOTHING;  -- 既に存在する場合はスキップ
