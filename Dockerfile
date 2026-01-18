# Dockerfile para Shard Cloud
FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache otimizado)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor porta (Shard Cloud geralmente usa 8080 ou 3000)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Comando de inicialização (ENTRYPOINT)
CMD ["python", "main.py"]
