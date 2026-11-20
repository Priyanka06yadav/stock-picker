
FROM python:3.11-slim

WORKDIR /workspace

# Install application and testing dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    streamlit \
    pytest \
    httpx

CMD ["python", "--version"]
