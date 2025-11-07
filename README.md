# VPBank Hybrid Cloud Platform
## Nền tảng quản lý hạ tầng đám mây thông minh

---

## 🌟 Giới Thiệu

**VPBank Hybrid Cloud Platform** là một giải pháp toàn diện giúp doanh nghiệp dễ dàng triển khai và quản lý hạ tầng đám mây trên AWS. Hệ thống được thiết kế với triết lý "đơn giản hóa phức tạp", mang đến trải nghiệm quản lý hạ tầng trực quan và hiệu quả.

### 🎯 Tại sao chọn chúng tôi?

- **🚀 Triển khai nhanh chóng**: Chỉ với vài cú click, bạn có thể tạo ra một hạ tầng hoàn chỉnh trên AWS
- **🤖 AI thông minh**: Hệ thống tự động đưa ra khuyến nghị scaling dựa trên dữ liệu thực tế
- **📊 Giám sát toàn diện**: Tích hợp sẵn Grafana, Mimir, Loki để theo dõi hiệu suất 24/7
- **💰 Tối ưu chi phí**: Tự động scale up/down để tiết kiệm chi phí vận hành
- **🔧 Dễ sử dụng**: Giao diện API thân thiện, documentation chi tiết

---

## ✨ Tính Năng Nổi Bật

### 🏗️ **Triển Khai Hạ Tầng Tự Động**
- Tạo VPC, EC2 instances, Load Balancer chỉ trong vài phút
- Cấu hình bảo mật tự động theo best practices
- Hỗ trợ nhiều region AWS khác nhau

### 📈 **Scaling Thông Minh với AI**
- AI Advisor phân tích metrics và đưa ra khuyến nghị
- Tự động scale up khi traffic tăng cao
- Scale down thông minh để tiết kiệm chi phí
- Hỗ trợ scaling thủ công khi cần thiết

### 🖥️ **Quản Lý EC2 Linh Hoạt**
- Start/Stop/Reboot instances từ xa
- Theo dõi trạng thái real-time
- Quản lý theo từng stack hoặc instance riêng lẻ

### 📊 **Monitoring & Analytics**
- Dashboard Grafana tích hợp sẵn
- Metrics CPU, Memory, Network real-time
- Log aggregation với Loki
- Custom queries và alerts

---

## 🏢 Ứng Dụng Thực Tế

### **E-commerce & Retail**
- Xử lý traffic cao trong các đợt sale lớn
- Tự động scale khi có flash sale
- Giám sát performance để đảm bảo UX tốt

### **Fintech & Banking**
- Đảm bảo uptime 99.9% cho các ứng dụng tài chính
- Scaling nhanh chóng khi có giao dịch đột biến
- Monitoring chi tiết để compliance

### **Media & Content**
- Xử lý traffic không đều trong ngày
- Tối ưu chi phí khi traffic thấp
- Scale nhanh khi có viral content

### **Enterprise Applications**
- Quản lý nhiều môi trường (dev, staging, prod)
- Tự động hóa deployment và scaling
- Centralized monitoring cho toàn bộ hệ thống

---

## 🚀 Bắt Đầu Nhanh

### Bước 1: Chuẩn bị môi trường
```bash
# Clone project
git clone <repository-url>
cd hybrid-cloud-platform

# Tạo virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt dependencies
pip install -r backend/requirements.txt
```

### Bước 2: Cấu hình AWS
```bash
# Cấu hình AWS credentials
aws configure

# Tạo file environment
cp .env.example .env
# Chỉnh sửa .env với thông tin của bạn
```

### Bước 3: Khởi chạy hệ thống
```bash
# Chạy backend server
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### Bước 4: Triển khai infrastructure đầu tiên
```bash
# Gọi API để tạo hạ tầng
curl -X POST http://localhost:8000/elb/deploy \\
  -H "Content-Type: application/json" \\
  -d '{
    "name_prefix": "my-app",
    "instance_count": 2,
    "instance_type": "t3.medium",
    "auto_install_monitoring": true
  }'
```

🎉 **Chúc mừng!** Bạn đã có một hạ tầng hoàn chỉnh với monitoring tự động!

---

## 📚 Tài Liệu

- **[📖 Hướng Dẫn Cài Đặt Chi Tiết](SETUP-GUIDE.md)** - Cài đặt từ A-Z
- **[🔌 API Documentation](API-DOCS-FRONTEND.md)** - Tài liệu API cho developers
- **[🌐 Interactive API Docs](http://localhost:8000/docs)** - Swagger UI (khi server đang chạy)

---

## 🏗️ Kiến Trúc Hệ Thống

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   AWS Cloud     │
│   Dashboard     │◄──►│   FastAPI       │◄──►│   EC2 + NLB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   AI Advisor    │
                       │   Gemini API    │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Monitoring    │
                       │ Grafana + Mimir │
                       │     + Loki      │
                       └─────────────────┘
```

---

## 🤝 Đóng Góp

Chúng tôi luôn chào đón các đóng góp từ cộng đồng! 

### Cách thức đóng góp:
1. **Fork** repository này
2. Tạo **feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. Mở **Pull Request**

### Báo lỗi:
- Mở **Issue** với mô tả chi tiết
- Cung cấp logs và steps to reproduce
- Tag với label phù hợp

---

## 🔒 Bảo Mật

- ✅ AWS credentials được lưu trữ an toàn trong `.env`
- ✅ Terraform state được quản lý cẩn thận
- ✅ Network security groups được cấu hình tự động
- ✅ SSH keys được tạo và quản lý tự động

**Lưu ý**: Đây là phiên bản development. Với production, hãy cân nhắc:
- Sử dụng AWS IAM roles thay vì access keys
- Remote backend cho Terraform state
- SSL/TLS cho API endpoints
- Network segmentation và VPN

---

## 📊 Thống Kê Project

- **🐍 Language**: Python 3.8+
- **⚡ Framework**: FastAPI
- **☁️ Cloud**: AWS (EC2, VPC, NLB)
- **🏗️ IaC**: Terraform
- **📊 Monitoring**: Grafana + Mimir + Loki
- **🤖 AI**: Google Gemini API
- **📦 Deployment**: Docker-ready

---

## 📞 Liên Hệ & Hỗ Trợ

- **📧 Email**: support@vpbank-cloud.com
- **💬 Slack**: #vpbank-cloud-platform
- **📱 Hotline**: 1900-xxxx
- **🌐 Website**: https://cloud.vpbank.com.vn

---

## 📄 Giấy Phép

Dự án này được phát hành dưới giấy phép **MIT License**. Xem file [LICENSE](LICENSE) để biết thêm chi tiết.

---

## 🙏 Lời Cảm Ơn

Cảm ơn tất cả những người đã đóng góp vào dự án này:

- **VPBank Technology Team** - Core development
- **AWS Solutions Architects** - Architecture guidance  
- **Open Source Community** - Tools và libraries
- **Beta Testers** - Feedback và bug reports

---

<div align="center">

**⭐ Nếu project này hữu ích, hãy cho chúng tôi một star! ⭐**

Made with ❤️ by VPBank Technology Team

</div>