# ---- Giai đoạn 1: Build ----
# Cài đặt Poetry và các gói phụ thuộc
FROM python:3.13-slim AS builder

# Cài đặt các biến môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cài đặt poetry
RUN pip install poetry

# Tạo thư mục làm việc
WORKDIR /code

# Copy file quản lý của poetry
COPY poetry.lock pyproject.toml ./

# Cấu hình poetry để tạo virtualenv trong thư mục dự án
RUN poetry config virtualenvs.create false && poetry install --no-root

# --- THÊM VÀO ---
# Cài đặt các gói build-time cần thiết để biên dịch mysqlclient
# 'build-essential' chứa các trình biên dịch C/C++
# 'pkg-config' dùng để tìm các thư viện hệ thống
# 'default-libmysqlclient-dev' & 'python3-dev' là các file header/dev
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    python3-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
# --- KẾT THÚC THÊM VÀO ---

# Cài đặt các gói phụ thuộc (bây giờ sẽ thành công)
RUN poetry install --no-root


# ---- Giai đoạn 2: Final ----
# Tạo image cuối cùng để chạy
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Cài các package build-time cần thiết
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    default-libmysqlclient-dev \
    python3-dev \
    libmariadb3 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY poetry.lock pyproject.toml ./
RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-root

COPY . .

EXPOSE 8000
