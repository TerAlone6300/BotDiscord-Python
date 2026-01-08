## 🚀 Hướng dẫn cấu hình và chạy bot

Làm theo từng bước bên dưới, không cần biết nhiều về Python.

---

## 1️⃣ Cấu hình bot

### Bước 1: Mở file `bot.py`

Trong thư mục project, mở file `bot.py` và tìm các biến sau:

```python
BOTTOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789
```

### Bước 2: Chỉnh sửa lại cho đúng

- `BOTTOKEN`: thay bằng token bot Discord của bạn
- `OWNER_ID`: thay bằng Discord ID của bạn

Ví dụ:

```python
BOTTOKEN = "MTExxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
OWNER_ID = 123456789012345678
```

⚠️ LƯU Ý QUAN TRỌNG
- Tuyệt đối KHÔNG public bot token
- KHÔNG commit token lên GitHub
- Nếu lỡ lộ token → reset ngay trong Discord Developer Portal

---

## 2️⃣ Cài thư viện và chạy bot

### Trên Windows

Chạy file:

```
start.bat
```

### Trên Linux / macOS / Termux

Cấp quyền chạy (chỉ cần làm 1 lần):

```
chmod +x start
```

Sau đó chạy:

```
./start
```

Script sẽ tự động:
- Cài thư viện từ `requirements.txt`
- Hiển thị bước `git pull` (đang tắt để bạn tự chỉnh)
- Chạy bot bằng `bot.py`

---

## 3️⃣ Bật git pull (tuỳ chọn)

Mở file `start.bat` hoặc `start`, tìm dòng:

```
git pull
```

Hiện tại dòng này đang bị comment để tránh lỗi.
Nếu bạn dùng git và muốn tự động update code, hãy bỏ comment dòng này.

---

## 4️⃣ Lỗi thường gặp

- `ModuleNotFoundError`
→ Chưa cài đủ thư viện, kiểm tra `requirements.txt`

- `Invalid token`
→ Token sai hoặc đã bị reset

- Bot không online
→ Kiểm tra bot đã bật trong Discord Developer Portal chưa

---

Chúc bạn chạy bot thành công 🚀
Nếu có lỗi, cứ mở issue hoặc hỏi thẳng, đừng ngại.
