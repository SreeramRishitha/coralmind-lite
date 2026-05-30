FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl tar && \
    curl -L https://github.com/withcoral/coral/releases/download/v0.4.1/coral-x86_64-unknown-linux-gnu.tar.gz -o coral.tar.gz && \
    tar -xzf coral.tar.gz && \
    chmod +x coral && \
    rm coral.tar.gz
COPY . .
RUN mkdir -p /root/.config/withcoral/coral/config && \
    cp coral-config.toml /root/.config/withcoral/coral/config/config.toml
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]