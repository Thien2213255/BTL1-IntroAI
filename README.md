# 🧩 Sokoban Game Solver

Game Sokoban cổ điển với AI solver tự động, viết bằng Python.

## 🚀 Cài Đặt & Chạy Game
Sử dụng python 3.13.x
**Chỉ cần chạy**:
```bash
python sokoban_solver.py
```

Chương trình đã bao gồm sẵn testcase mặc định, không cần file level bên ngoài!

## 🎮 Cách Chơi

### Điều Khiển
- **Mũi tên** hoặc **nút điều hướng**: Di chuyển
- **Click chuột**: Di chuyển đến ô liền kề
- **Reset**: Chơi lại từ đầu
- **Auto Solve**: AI tự giải (BFS hoặc A*)


## 🧠 Tính Năng

- ✅ Giao diện đồ họa với Tkinter
- ✅ 2 giải thuật AI: BFS và A*
- ✅ Testcase mặc định có sẵn
- ✅ Theo dõi hiệu suất: thời gian & bộ nhớ
- ✅ Điều khiển bằng bàn phím hoặc chuột

## 📁 Sử Dụng Level Riêng (Tùy chọn)

Nếu muốn dùng level khác, tạo file trong thư mục `testcases/` và sửa dòng code cuối:
```python
app = SokobanUI(root, level_file='./testcases/your_level.txt')
```

---

*Chúc bạn chơi game vui vẻ! 🎯*