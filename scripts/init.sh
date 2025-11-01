#!/bin/bash
set -euxo pipefail
if command -v apt-get >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y nginx
  systemctl enable nginx || true
  systemctl start nginx || true
elif command -v yum >/dev/null 2>&1; then
  yum install -y nginx || amazon-linux-extras install -y nginx1 || dnf install -y nginx || true
  systemctl enable nginx || true
  systemctl start nginx || true
fi
echo "Hello from $(hostname)" > /var/www/html/index.html || echo "Hello" > /usr/share/nginx/html/index.html || true
