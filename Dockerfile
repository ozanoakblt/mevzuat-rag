FROM python:3.13-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Bağımlılıkları önce kopyala → kod değişince pip install cache'i bozulmasın
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje kodu + data (senin tercihin: vector store image'e gömülü)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]