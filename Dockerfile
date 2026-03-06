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

# 6. Install ONLY the Chromium browser (DO NOT use --with-deps here!)
RUN playwright install chromium

# 7. Copy your actual project code into the container
COPY . .

# 8. Set the exact Lambda execution entry point
CMD [ "main.lambda_handler" ]