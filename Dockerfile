# 使用官方 Python 映像作為基礎映像
FROM python:3.9

# 設置工作目錄
WORKDIR /app

# 複製需求文件並安裝依賴
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 安裝 Node.js 和 npm (為了使用 firebase-tools)
RUN apt-get update && \
    apt-get install -y nodejs npm && \
    npm install -g firebase-tools

# 複製應用程式代碼到容器中
COPY . .

# 設置環境變量
ENV HOST 0.0.0.0
ENV PORT 8080

# 暴露應用程式的端口
EXPOSE 8080

# 定義啟動命令
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8080"]
