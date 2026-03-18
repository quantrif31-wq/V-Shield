Xin chào tất cả các bạn!

Cảm ơn vì đã chú ý đến dự án của chúng tôi

nó để làm gì thì ai cũng biết mà nhỉ?

ta đến phần cách chạy luôn



B1) Đảm bảo đường dẫn dự án sau khi clone phải là C:\\DoAnTotNghiep\\V-Shield

 	Nếu không phải thì vào ổ C tạo thư mục DoAnTotNghiep sau đó dán cả cái thư mục V-Shield

 	đã clone về vào đấy.

B2) vào đường dẫn C:\\DoAnTotNghiep\\V-Shield rồi click 2 lần vào tệp taomoitruong.bat để chạy nó

B3) Tiếp tục ở vị trí bước 2 ta click 2 lần vào tệp run.bat để có thể chạy toàn bộ dự án



phần mã phòng trường hợp cần chạy thủ công (chỉ có bậc đại đế chân chính mới có thể sử dụng được)



python -m venv venv

venv\\Scripts\\activate

pip install -r requirements.txt

python lpr\_ipcam.py

uvicorn FaceID:app --reload --port 8000



pip freeze > requirements.txt

lpr\_gpu\\Scripts\\activate



pip cache purge

pip install pyodbc

