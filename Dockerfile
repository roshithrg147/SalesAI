# 1. Base Image: Amazon Linux 2023 / Python 3.12
FROM public.ecr.aws/lambda/python:3.12

# 2. Install all required C-compilers and Playwright system dependencies via dnf
RUN dnf install -y \
    gcc \
    gcc-c++ \
    alsa-lib \
    atk \
    at-spi2-atk \
    at-spi2-core \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    pango \
    libdrm \
    libxkbcommon \
    nss \
    xorg-x11-server-Xvfb \
    mesa-libgbm \
    unzip

# 3. Set the working directory to the Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# 4. Copy requirements and upgrade pip
COPY requirements.txt .
RUN pip install --upgrade pip

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 6. Install Playwright and force Chromium into the global path
RUN pip install playwright && \
    playwright install chromium --with-deps

# 7. Copy your actual project code into the container
COPY . ${LAMBDA_TASK_ROOT}

# Set permissions (Crucial for Lambda execution)
RUN chmod -R 755 /ms-playwright

# 8. Set the exact Lambda execution entry point
CMD [ "main.lambda_handler" ]