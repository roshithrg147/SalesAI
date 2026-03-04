# Use the official AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies required for Playwright and Chromium
# These are necessary for the browser to render headlessly in the Lambda environment
RUN yum install -y \
    atk \
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
    at-spi2-atk \
    libdrm \
    libgbm \
    libxshmfence \
    alsa-lib \
    mesa-libgbm \
    unzip \
    && yum clean all

# Set the working directory to the Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and the Chromium browser binary
# We only install chromium to keep the image size smaller
RUN playwright install chromium --with-deps

# Copy all project files into the container
COPY . .

# Set the Lambda handler mapping for AWS invocation
CMD ["main.lambda_handler"]