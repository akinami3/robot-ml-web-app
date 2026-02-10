FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate Python protobuf code from fleet.proto
RUN python -m grpc_tools.protoc \
    -I./proto \
    --python_out=./app/grpc_client \
    --grpc_python_out=./app/grpc_client \
    ./proto/fleet.proto

# Fix import path in generated grpc file (fleet_pb2 -> .fleet_pb2 for package import)
RUN sed -i 's/^import fleet_pb2 as fleet__pb2$/from . import fleet_pb2 as fleet__pb2/' app/grpc_client/fleet_pb2_grpc.py

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expose ports (REST API + gRPC data recording)
EXPOSE 8000 50052

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
