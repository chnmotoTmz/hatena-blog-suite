echo All blog containers started.
@echo off
echo ==== 停止処理 ====
docker compose -f docker-compose.blog1.yml down
docker compose -f docker-compose.blog2.yml down
echo All blog containers stopped.

echo ==== 起動・ビルド処理 ====
docker compose -f docker-compose.blog1.yml build
docker compose -f docker-compose.blog1.yml up -d
docker compose -f docker-compose.blog2.yml build
docker compose -f docker-compose.blog2.yml up -d
echo All blog containers started.
