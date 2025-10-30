# 1. Usar uma imagem base oficial do Python (versão 'slim' para ser mais leve)
FROM python:3.10-slim

# 2. Definir o diretório de trabalho dentro do contentor
WORKDIR /app

# 3. Instalar as dependências primeiro (para aproveitar o cache do Docker)
# Copiar o ficheiro de requisitos
COPY requirements.txt .

# Instalar as dependências de produção
# gunicorn é um servidor WSGI de produção (melhor que o servidor de debug do Flask)
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar os ficheiros da aplicação para o diretório de trabalho
COPY app.py .
COPY hfmea2.csv .
COPY templates/ templates/

# 5. Expor a porta 5000 (definida no seu app.py e no comando CMD)
EXPOSE 5000

# 6. Definir o comando para executar a aplicação quando o contentor iniciar
# Usamos o gunicorn para servir a aplicação 'app' a partir do ficheiro 'app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
