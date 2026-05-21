# Hướng dẫn Tích hợp Kiro Agent với Aether AI Gateway

Chào mừng bạn đến với tài liệu hướng dẫn tích hợp **Kiro Agent** làm LLM Engine thông qua **Aether AI Gateway** của bạn. 

Việc tích hợp này sẽ giúp bạn tận dụng **20.000.000 tokens miễn phí** từ **Doubleword AI** (chạy model suy luận cao cấp `moonshotai/Kimi-K2.6` hoặc `deepseek-ai/DeepSeek-V4-Pro`) cùng cơ chế failover định tuyến thông minh của Gateway để chạy các Agent lập trình mà **không tốn một đồng chi phí API nào**.

---

## 🛠️ THÔNG TIN KẾT NỐI GATEWAY CỦA BẠN
Khi Gateway đang chạy cục bộ (local):
* **Base URL:** `http://localhost:8000/v1`
* **Endpoint Completions:** `http://localhost:8000/v1/chat/completions`
* **API Key:** `free-gateway-key` *(Nếu bạn không bật GATEWAY_SECRET trong file `.env`, bạn có thể điền bất kỳ chuỗi ký tự nào)*
* **Model khuyến nghị cho Kiro:** `moonshotai/Kimi-K2.6` (được tối ưu hóa cho reasoning và coding) hoặc `deepseek-ai/DeepSeek-V4-Pro`.

---

## 📋 CÁC TUỲ CHỌN TRIỂN KHAI (Vui lòng chọn 1 trong các cách sau)

### 👉 Tuỳ chọn 1: Cấu hình thông qua Biến Môi Trường (System Environment)
Nếu bạn đang chạy **Kiro Agent** dưới dạng **CLI (Command Line)** hoặc **Script độc lập**, đây là cách nhanh nhất và tối ưu nhất.

1. **Đối với macOS/Linux (Terminal/Zsh):**
   Mở terminal của bạn và chạy lệnh sau trước khi khởi động Kiro Agent:
   ```bash
   export OPENAI_API_BASE="http://localhost:8000/v1"
   export OPENAI_API_KEY="free-gateway-key"
   export LLM_MODEL="moonshotai/Kimi-K2.6" # Hoặc model bạn muốn dùng
   ```

2. **Cấu hình vĩnh viễn (Optional):**
   Nếu bạn muốn cấu hình này tự động tải mỗi khi mở Terminal, hãy thêm các dòng trên vào file cấu hình shell của bạn (`~/.zshrc` hoặc `~/.bash_profile`):
   ```bash
   echo 'export OPENAI_API_BASE="http://localhost:8000/v1"' >> ~/.zshrc
   echo 'export OPENAI_API_KEY="free-gateway-key"' >> ~/.zshrc
   echo 'export LLM_MODEL="moonshotai/Kimi-K2.6"' >> ~/.zshrc
   source ~/.zshrc
   ```

---

### 👉 Tuỳ chọn 2: Cấu hình trong File `.env` của Kiro Agent
Nếu **Kiro Agent** là một project có chứa file cấu hình `.env` riêng biệt:

1. Tìm file `.env` nằm trong thư mục cài đặt/chạy của Kiro Agent.
2. Thêm hoặc cập nhật các dòng cấu hình sau:
   ```env
   # Trỏ API của Kiro Agent về Gateway cục bộ của bạn
   OPENAI_API_BASE=http://localhost:8000/v1
   OPENAI_API_KEY=free-gateway-key
   
   # Chỉ định model coding/reasoning qua Gateway
   KIRO_MODEL=moonshotai/Kimi-K2.6
   ```

---

### 👉 Tuỳ chọn 3: Cấu hình trong Cài đặt IDE (VS Code / Cursor / Windsurf / Kiro IDE)
Nếu bạn chạy **Kiro Agent** thông qua một Extension (Tiện ích mở rộng) của IDE hoặc một IDE độc lập:

1. **Mở Settings (Cài đặt):**
   * Trong VS Code/Cursor: Nhấn `Cmd + ,` (macOS) hoặc `Ctrl + ,` (Windows/Linux).
   * Tìm kiếm từ khoá `Kiro` hoặc `Custom OpenAI Endpoint`.

2. **Cập nhật các giá trị:**
   * **OpenAI Base URL / API Path:** Điền `http://localhost:8000/v1`
   * **API Key:** Điền `free-gateway-key`
   * **Model:** Điền `moonshotai/Kimi-K2.6`

---

### 👉 Tuỳ chọn 4: Cấu hình File JSON Config của Kiro Agent (`config.json`)
Một số agent hỗ trợ file cấu hình định dạng JSON tại thư mục gốc người dùng hoặc thư mục cài đặt (ví dụ `~/.kiro/config.json`):

1. Tạo hoặc chỉnh sửa file cấu hình JSON của Kiro:
   ```json
   {
     "llm": {
       "provider": "openai",
       "base_url": "http://localhost:8000/v1",
       "api_key": "free-gateway-key",
       "model": "moonshotai/Kimi-K2.6"
     }
   }
   ```

---

## 🚀 HƯỚNG DẪN KIỂM TRA KẾT NỐI
Sau khi bạn đã chọn và cấu hình một trong các tuỳ chọn trên:

1. **Khởi động AI Gateway cục bộ:**
   * Đảm bảo Gateway đang chạy ở port 8000 bằng cách mở một Terminal mới trong thư mục `free-ai-gateway` và chạy:
     ```bash
     # Nếu dùng python virtualenv
     source .venv/bin/activate
     python -m app.main
     ```
   * Kiểm tra xem Gateway có hoạt động không bằng cách truy cập: `http://localhost:8000/health` trên trình duyệt.

2. **Chạy Kiro Agent và Thực hiện Lập trình:**
   * Hãy yêu cầu Kiro viết một đoạn code ngắn (ví dụ: *"Write a fibonacci function in Python"*).
   * Xem log trên cửa sổ Terminal của AI Gateway. Bạn sẽ thấy các dòng log báo request trúng vào endpoint `/v1/chat/completions`, sau đó được định tuyến qua `Doubleword` với model `moonshotai/Kimi-K2.6`!

---

> [!TIP]
> **Mẹo Tối Ưu:** Model `moonshotai/Kimi-K2.6` là dòng model reasoning (suy luận). Khi Kiro Agent gửi các tác vụ phức tạp, model này sẽ sinh ra các "thinking tokens" rất chất lượng giúp code chính xác hơn. Gateway đã được cấu hình pricing `(0.0, 0.0)` cho Doubleword để đảm bảo mày có thể thoải mái sử dụng mà không lo hết ngân sách ảo của hệ thống!
