# ---- Base image ----
FROM python:3.11-slim

# ---- Working directory ----
WORKDIR /app

# ---- Copy files ----
COPY . .

# ---- Install dependencies ----
RUN pip install --no-cache-dir -r requirements.txt

# ---- Expose FastAPI port ----
EXPOSE 8080

# ---- Start FastAPI app ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
