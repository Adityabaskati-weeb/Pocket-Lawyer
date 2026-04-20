FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e .

ENV PYTHONPATH=/app/src
ENV POCKET_LAWYER_STORE=/tmp/pocket-lawyer-reports.json
ENV POCKET_LAWYER_BUILD=single-3d-ui-20260420

EXPOSE 7860

CMD ["python", "-m", "pocket_lawyer.api", "--host", "0.0.0.0", "--port", "7860"]
