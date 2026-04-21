"""
EWI EasyPlay - GitHub Actions CI/CD 配置
自動化測試、構建和部署
"""

# .github/workflows/ci-cd.yml 內容

cicd_workflow = """
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 0 * * 0'  # 每週日午夜執行

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # 代碼質量檢查
  code_quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black pylint pytest pytest-cov

      - name: Lint with flake8
        run: |
          flake8 backend/ --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 backend/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

      - name: Format check with black
        run: black --check backend/

      - name: Run pylint
        run: |
          find backend/ -name '*.py' | xargs pylint --disable=all --enable=E,F || true

  # 單元測試
  unit_tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests
        run: |
          cd backend
          pytest tests/ -v --cov=core --cov=services --cov=integrations --cov-report=xml
        env:
          CELERY_BROKER_URL: redis://localhost:6379/0
          CELERY_RESULT_BACKEND: redis://localhost:6379/1

      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
          flags: unittests
          name: codecov-umbrella

  # 集成測試
  integration_tests:
    runs-on: ubuntu-latest
    needs: unit_tests
    services:
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt
          pip install pytest pytest-asyncio

      - name: Run integration tests
        run: |
          cd backend
          pytest tests/test_phase2.py::TestIntegration -v -s
        env:
          CELERY_BROKER_URL: redis://localhost:6379/0
          CELERY_RESULT_BACKEND: redis://localhost:6379/1

  # Docker 構建
  build_docker:
    runs-on: ubuntu-latest
    needs: unit_tests
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push Docker image
        uses: docker/build-push-action@v4
        with:
          context: ./backend
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # 部署到測試環境
  deploy_staging:
    runs-on: ubuntu-latest
    needs: [unit_tests, integration_tests, build_docker]
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # 實現部署邏輯

      - name: Run smoke tests
        run: |
          echo "Running smoke tests on staging..."
          # 實現冒煙測試

  # 部署到生產環境
  deploy_production:
    runs-on: ubuntu-latest
    needs: [unit_tests, integration_tests, build_docker]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    environment:
      name: production
      url: https://ewi.paul720810.dpdns.org

    steps:
      - uses: actions/checkout@v3

      - name: Deploy to production
        run: |
          echo "Deploying to production environment..."
          # 實現生產部署邏輯

      - name: Run health checks
        run: |
          echo "Running health checks on production..."
          # 實現健康檢查

      - name: Notify deployment
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment: ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
"""

# Docker 配置
dockerfile_content = """
FROM python:3.9-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    libsndfile1 \\
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . .

# 建立日誌目錄
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')"

# 啟動應用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# Docker Compose 配置
docker_compose_content = """
version: '3.9'

services:
  # Redis - 消息代理和結果後端
  redis:
    image: redis:7-alpine
    container_name: ewi-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5

  # FastAPI 應用
  api:
    build: ./backend
    container_name: ewi-api
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Celery 工人
  celery_worker:
    build: ./backend
    container_name: ewi-celery-worker
    command: celery -A services.task_queue.celery_app worker -l info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
      - api
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./logs:/app/logs

  # Celery Beat - 定時任務
  celery_beat:
    build: ./backend
    container_name: ewi-celery-beat
    command: celery -A services.task_queue.celery_app beat -l info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
      - api
    volumes:
      - ./backend:/app
      - ./logs:/app/logs

volumes:
  redis_data:

networks:
  default:
    name: ewi-network
"""

print("CI/CD 配置已生成")
print(f"GitHub Actions Workflow: {len(cicd_workflow)} 字符")
print(f"Dockerfile: {len(dockerfile_content)} 字符")
print(f"Docker Compose: {len(docker_compose_content)} 字符")
