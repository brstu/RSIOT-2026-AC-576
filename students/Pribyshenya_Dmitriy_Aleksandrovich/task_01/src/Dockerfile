# Multi-stage build
# Stage 1: Build stage
FROM python:3.12-alpine AS builder

LABEL org.bstu.student.fullname="Pribyshenya Dmitry Alexandrovich"
LABEL org.bstu.student.id="220245"
LABEL org.bstu.group="AS-576"
LABEL org.bstu.variant="17"
LABEL org.bstu.course="RSIOT"

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev

# Copy requirements and install in virtual environment
COPY app/requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage (минимальный)
FROM python:3.12-alpine

# Create non-root user
RUN adduser -D -u 65532 flaskuser

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY app/ .

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Student environment variables
ENV STU_ID=220245
ENV STU_GROUP=AS-576
ENV STU_VARIANT=17

# Set ownership
RUN chown -R flaskuser:flaskuser /app

# Switch to non-root user
USER flaskuser

# Expose port
EXPOSE 9051

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:9051/ready')" || exit 1

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:9051", "--workers", "2", "--threads", "4", "--timeout", "30", "--graceful-timeout", "15", "--access-logfile", "-", "--error-logfile", "-", "app:app"]