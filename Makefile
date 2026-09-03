.DEFAULT_GOAL := help

UV ?= uv
HOST ?= 0.0.0.0
PORT ?= 9000

.PHONY: help install dev run test

help: ## 显示可用命令
	@awk 'BEGIN {FS = ":.*##"}; /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## 安装项目依赖
	$(UV) sync

dev: ## 以热重载模式启动 FastAPI（默认 0.0.0.0:8000）
	$(UV) run uvicorn app.app:app --host $(HOST) --port $(PORT) --reload

run: ## 按 .env 中的 HOST、PORT 配置启动 FastAPI
	$(UV) run python main.py

test: ## 运行测试
	$(UV) run pytest
