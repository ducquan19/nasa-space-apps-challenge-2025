## 🛠 Cách cài đặt và sử dụng 🛠
1. Clone về máy: ở vscode, mở terminal, chuyển về thư mục của bạn, chạy lệnh: git clone  *[url repository]* hoặc tải file zip. Khi cần cập nhật lại sau khi dùng git clone xong thì thì chạy lệnh: git pull origin master.
2. Project sử dụng API key cá nhân của openWeather, vì mục đích bảo mật nên mình không để API key của mình (API này free, có giới hạn). Bạn cần tạo file mới là config.js ở cùng thư mục với file index.html và ghi vào file config.js như sau, YOUR API KEY sẽ có dạng thế này: 1234567c2190acb7d1531265b3ea55abcdef

>**export const apiKey = "YOUR API KEY";**

3. Bạn cần vào website Openweather, tạo tài khoản, nhấn vào profile, vào mục your API, có API, sao chép nó và để vào config.js

>*Với mục đích dự đoán thời tiết cần cài đặt và sử dụng Python trên máy*
4. Bạn cần biết phiên bản python của mình (đề phòng lỗi về thư viện): ở terminal Vscode dùng lệnh python --version, kết quả phiên bản của mình là Python 3.13.7
5. Mở file explorer, chọn vào thư mục model của project này trên máy, chuột phải và chọn "Open with code" để đưa con trỏ terminal của Vscode vào thư mục, ở cửa sổ Vscode này (sau khi cài đặt pip-là công cụ của python) chạy lệnh sau và chờ 10 phút nếu không có lỗi gì xảy ra
>**pip install -r requirement.txt**

6. Chạy lệnh sau để chạy back-end, tạo ra đường dẫn api ở cổng http://127.0.0.1:8000 trên máy tính
>**python -m uvicorn main:app --reload**

7. Quay lại cửa sổ Vscode chính của project, chọn nút go live để view trang web. 

## 🗺 Cấu trúc project 🗺

- Thư mục model dùng để chứa các thuật toán dự đoán dữ liệu 
- Thư mục data dùng để chứa các resoure, file dữ liệu, văn bản thông tin
- Thư mục image dùng để chứa ảnh, logo, icon
- *index.html* cấu trúc website chính
- *script.js* module gồm các lời gọi API từ nhiều nguồn và thao tác, nút bấm chính
- *map.js* module cấu hình bản đồ, các lớp, các thao tác
- *options.js* module cài đặt 4 tính năng quan trọng của website
- *config.js* chứa các biến toàn cục cài đặt cho chương trình
- *style.css* file điều chỉnh UI/UX

