# AI Gateway - Kiến trúc Router & Cơ chế Hosting

### Sơ đồ Kiến trúc & Luồng hoạt động (Architecture & Flow)

```mermaid
flowchart TD
    User([Người dùng]) -->|Gửi câu hỏi| UI[Frontend Chat UI\nlocalhost:5173]
    UI -->|Gọi API| Backend{AI Gateway Backend\n(localhost:8000)}
    
    subgraph Local Machine [Máy tính Local của bạn]
        Backend
        DB[(Database PostgreSQL\nLưu Token & Tiền)]
        Env[.env File\nChứa API Keys Bảo mật]
        
        Backend <--> DB
        Backend -. Đọc Key bí mật .-> Env
    end
    
    subgraph Cloud Providers [Các Hãng AI Cloud]
        P1[1. Groq\nƯu tiên #1]
        P2[2. Gemini\nDự phòng #1]
        P3[3. GitHub\nDự phòng #2]
    end

    Backend == 1. Gọi thử Groq ==> P1
    P1 -. Lỗi/Sập/Quá tải .-x Backend
    Backend == 2. Bắt lỗi, tự động Failover ==> P2
    P2 -- 3. Trả kết quả thành công --> Backend
    Backend -- 4. Lưu lịch sử & Cảnh báo Toast --> DB
    Backend -- 5. Trả kết quả mượt mà --> UI
```

---

## 1. Luồng Router (Cơ chế Failover Tự động)

Luồng Router được thiết kế để đảm bảo hệ thống AI không bao giờ bị sập (Zero Downtime) khi phục vụ người dùng. Nó hoạt động theo nguyên tắc **Chained Fallback** (Chuyển tiếp theo chuỗi):

1. **Tiếp nhận Request:** Khi người dùng gửi một câu hỏi từ giao diện Chat, Backend (FastAPI) sẽ nhận request này.
2. **Thử nghiệm Provider ưu tiên (Primary):** Router sẽ lấy danh sách các nhà cung cấp (Providers) theo thứ tự ưu tiên (Ví dụ: 1. Groq, 2. Gemini, 3. GitHub). Nó sẽ gọi API của thằng số 1 (Groq) trước.
3. **Phát hiện lỗi & Chuyển hướng (Failover):** 
   - Nếu Groq phản hồi thành công, Router trả kết quả ngay lập tức cho người dùng.
   - Nếu Groq bị lỗi (hết tiền, sập server, rate limit), Router **ngay lập tức** "bắt" lấy lỗi đó, chặn không cho báo lỗi lên UI. Nó tự động động đổi sang Provider số 2 (Gemini).
4. **Tự động Map Model (Auto Model Mapping):** Khi đổi từ Groq sang Gemini, Router đủ thông minh để tự đổi tên model từ `llama3-70b` (của Groq) sang `gemini-1.5-flash` (của Gemini) để tránh lỗi không tương thích.
5. **Ghi nhận lịch sử (Telemetry):** Mọi cú "quay xe" (failover) đều được ghi lại (Failover Trace) vào Database để Admin biết được hệ thống đã phải chuyển hướng bao nhiêu lần. Đồng thời, một cảnh báo nhỏ (Toast) sẽ hiện lên UI cho người dùng biết.

---

## 2. Các Provider (Nhà Cung Cấp AI)

Hệ thống Gateway đóng vai trò như một "nhà ga trung tâm" kết nối nhiều hãng AI khác nhau. Hiện tại hệ thống hỗ trợ các Provider sau:
- **Groq:** Tốc độ phản hồi cực nhanh (dùng Llama).
- **Gemini (Google):** Thông minh, xử lý đa phương tiện tốt.
- **GitHub Models:** Dùng làm phương án dự phòng (Fallback) cực kỳ ổn định.
- **OpenAI:** Phục vụ các task yêu cầu độ phức tạp cao (GPT-4o).

Thông tin của các Provider (Tên model mặc định, thứ tự ưu tiên) được định nghĩa linh hoạt trong file `providers.json`.

---

## 3. Cách hệ thống Host "mọi Provider" trên máy của bạn

Thực chất, bạn **không** tải và chạy các mô hình AI nặng hàng chục GB (như GPT-4 hay Llama) trực tiếp trên ổ cứng Macbook của bạn. Điều đó là bất khả thi. Thay vào đó, kiến trúc hoạt động như sau:

*   **Host Gateway Backend (Local Proxy):** Bạn đang host mã nguồn **AI Gateway Backend** (viết bằng Python/FastAPI) chạy trên máy tính của bạn (tại `localhost:8000`).
*   **Quản lý API Key Tập Trung:** Máy tính của bạn (cụ thể là file `.env` nằm sâu trong máy) sẽ nắm giữ toàn bộ các **chìa khoá (API Keys)** của Groq, Gemini, GitHub. 
*   **Giao tiếp gián tiếp (Proxying):** 
    - Frontend (Giao diện Chat) không bao giờ kết nối thẳng ra ngoài internet đến OpenAI hay Groq. Nó chỉ kết nối vào Backend trên máy bạn.
    - Backend trên máy bạn sẽ dùng các API Keys trong file `.env`, đứng ra làm "đại diện" gửi câu hỏi lên Cloud của Groq/Gemini.
    - Sau khi Cloud trả kết quả về máy bạn, máy bạn mới đưa kết quả lên giao diện cho người dùng xem.

**Lợi ích của việc Host Gateway trên máy Local:**
1. **Bảo mật tuyệt đối:** API Keys (tiền của bạn) nằm an toàn trên máy bạn, không bao giờ bị rò rỉ ra Frontend cho người ngoài thấy.
2. **Kiểm soát lưu lượng:** Máy của bạn đứng ở giữa sẽ đếm được số Tokens, tính được tiền (Cost), và chặn được những người dùng xài lố ngân sách.
3. **Giấu nhẹm việc Failover:** Người dùng cuối không hề biết hệ thống đằng sau vừa sập và phải đổi sang hãng khác, họ chỉ thấy kết quả luôn được trả về mượt mà.

---

## 4. Chi tiết Cơ chế Cốt lõi của Backend (Dành cho Quản lý & Kỹ thuật)

Backend của AI Gateway được xây dựng bằng ngôn ngữ **Python** và framework **FastAPI**, được thiết kế để chịu tải cao (High Performance) và xử lý bất đồng bộ (Asynchronous). Cục Backend này đóng vai trò như một "bộ não" kiểm soát toàn bộ hệ thống với các tính năng sau:

### 4.1. Tiêu chuẩn hoá giao tiếp (Unified API)
- Mỗi hãng AI (Google, OpenAI, Groq) đều có cấu trúc API khác nhau. 
- Thay vì bắt Frontend phải nhớ cách giao tiếp với từng hãng, **Backend đóng vai trò "Phiên dịch viên"**. Nó ép tất cả mọi thứ về một tiêu chuẩn chung. Frontend chỉ cần code 1 kiểu, còn việc "nói chuyện" với Google hay Groq sẽ do Backend tự lo.

### 4.2. Hệ thống Thống kê & Kế toán (Analytics & Telemetry)
- Cứ mỗi lần AI nhả ra 1 chữ (Token), Backend đều ghi nhận lại. Mọi dữ liệu như: Thời gian phản hồi (Latency), Số Token (Usage), Số tiền quy đổi (Cost) đều được lưu vào cơ sở dữ liệu **PostgreSQL (Supabase)**.
- Từ đó, Backend cấp dữ liệu chuẩn 100% thời gian thực cho **Admin Dashboard**, giúp người quản trị thấy ngay lập tức hãng nào đang tốn nhiều tiền nhất và ai là người dùng nhiều nhất.

### 4.3. Quản lý Bộ nhớ & Bối cảnh (Session & Context)
- Backend lưu giữ mạch câu chuyện (Lịch sử chat).
- Điểm đắt giá nhất: Khi hệ thống tự động "quay xe" (Failover) từ Groq sang Gemini do lỗi, Backend sẽ **tự động bốc toàn bộ lịch sử chat ở Groq chuyển sang cho Gemini đọc**. Nhờ đó, dù AI vừa bị đổi, nó vẫn nhớ được người dùng đang nói gì trước đó, không bắt người dùng phải lặp lại câu hỏi cũ.

### 4.4. Tính sẵn sàng tích hợp NotebookLM & RAG
- Kiến trúc được thiết kế dạng Module (lắp ghép). Backend đã chuẩn bị sẵn "ổ cắm" (Endpoint) để sau này tích hợp các kho tài liệu nội bộ (PDF, File Word) qua công nghệ **RAG**. 
- Đây chính là cơ sở hạ tầng để tiến tới xây dựng một trợ lý AI đọc tài liệu chuyên sâu của công ty (tương tự Google NotebookLM) với dữ liệu bảo mật 100% không bị mang đi huấn luyện (train) trên mạng.
