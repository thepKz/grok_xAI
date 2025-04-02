# XBot GenZ 🔥

## Cảnh báo ⚠️
> **Chú ý**: Ứng dụng này có chứa ngôn ngữ GenZ, có thể bao gồm từ ngữ thô tục, chửi thề và nội dung dành cho người trưởng thành. Nếu bạn dưới 18 tuổi hoặc không thoải mái với các nội dung này, vui lòng cân nhắc trước khi sử dụng.

## Giới thiệu
XBot GenZ là chatbot tích hợp Grok API, sử dụng ngôn ngữ GenZ Việt Nam (tao-mày, slang, emoji), có khả năng:
- Chat như một người bạn GenZ cá tính
- Tạo ảnh từ mô tả của người dùng
- Phân tích ảnh người dùng tải lên
- Đánh giá nhan sắc theo thang điểm 100 và tiêu chuẩn GenZ

## Tính năng chính
- **Chat GenZ**: Sử dụng ngôn ngữ GenZ Việt Nam, đầy slang và emoji
- **Tạo ảnh**: Tạo ảnh từ mô tả hoặc tạo ảnh biến thể từ ảnh đã tải lên
- **Phân tích ảnh**: Mô tả chi tiết nội dung ảnh người dùng tải lên
- **Đánh giá nhan sắc**: Cho điểm và nhận xét nhan sắc theo tiêu chuẩn GenZ
- **Giao diện thân thiện**: Hỗ trợ dark mode và responsive design
- **Chửi khách hàng**: Hỗ trợ chửi nhau mà bạn xài Chatgpt chưa bao giờ gặp

## Cài đặt

### Yêu cầu
- Python 3.8+
- Grok API key (đăng ký tại [api.x.ai](https://api.x.ai))

### Các bước cài đặt
1. Clone repository
```bash
[git clone https://github.com/yourusername/xbot-genz.git](https://github.com/thepKz/grok_xAI.git)
cd xbot-genz
```

2. Cài đặt thư viện
```bash
pip install -r requirements.txt
```

3. Tạo file `.env` ở thư mục gốc và thêm API key của bạn
```
XAI_API_KEY=your_api_key_here
```

4. Chạy ứng dụng
```bash
python app.py
```

5. Truy cập web app tại `http://localhost:5000`

## Hướng dẫn sử dụng
- **Chat**: Gõ tin nhắn vào ô chat và nhấn Enter hoặc nút Gửi
- **Tải ảnh lên**: Nhấn nút hình ảnh trong khung chat rồi chọn ảnh
- **Tạo ảnh**: Nhấn nút Magic trong header, nhập mô tả và nhấn nút Tạo ảnh
- **Xem ảnh đầy đủ**: Nhấn vào ảnh để xem ở kích thước đầy đủ
- **Đánh giá nhan sắc**: Tải ảnh lên và hỏi "đánh giá nhan sắc giúp tao"
- **Tạo ảnh biến thể**: Tải ảnh lên và yêu cầu "tạo ảnh giống vậy nhưng..."

## Lưu ý
- API có giới hạn tạo 10 ảnh mỗi phiên chat
- Chatbot có thể đôi khi toxic hoặc sử dụng ngôn ngữ thô tục
- Không sử dụng cho mục đích tạo nội dung nhạy cảm hoặc vi phạm đạo đức

## Phát triển bởi
[Your Name/Team] - Sử dụng Grok API từ xAI
