# Structure Blueprint (LaTeX Report)

## Mục lục nội bộ
- [1. Mục tiêu tài liệu](#1-mục-tiêu-tài-liệu)
- [2. Khung báo cáo bắt buộc](#2-khung-báo-cáo-bắt-buộc)
- [3. Logic 4 chương nội dung](#3-logic-4-chương-nội-dung)
- [4. Quy tắc đánh số và thành phần](#4-quy-tắc-đánh-số-và-thành-phần)
- [5. Checklist triển khai LaTeX](#5-checklist-triển-khai-latex)
- [6. Dấu vết trích xuất](#6-dấu-vết-trích-xuất)

## 1. Mục tiêu tài liệu
Tài liệu này chuẩn hóa bố cục báo cáo mới để dùng làm source-of-truth khi scaffold LaTeX.
Phạm vi tập trung vào cấu trúc, thứ tự thành phần, quy tắc đánh số và yêu cầu hình thức.

## 2. Khung báo cáo bắt buộc
Thứ tự khuyến nghị:
1. Bìa và các trang thủ tục (bìa, phụ bìa, tóm tắt, cam đoan, cảm ơn, mục lục, danh mục ký hiệu/viết tắt nếu có).
2. Mở đầu (không đánh số chương).
3. Nội dung chính gồm 4 chương (đánh số chương 1..4).
4. Kết luận (không đánh số chương).
5. Tài liệu tham khảo.
6. Phụ lục (nếu có).

Quy định trọng yếu: phần Mở đầu và Kết luận không xem là chương, không đánh số chương.

## 3. Logic 4 chương nội dung
- Chương 1: Bối cảnh chủ đề, bài toán, input/output, related work nền tảng.
- Chương 2: Các mô hình/kỹ thuật tiên tiến liên quan trực tiếp bài toán.
- Chương 3: Mô hình đề xuất của đề tài và điểm sáng tạo.
- Chương 4: Thiết kế thực nghiệm, dữ liệu, kịch bản, độ đo, kết quả và nhận xét.

## 4. Quy tắc đánh số và thành phần
- Mục/tiểu mục dùng tối đa 3 cấp: `<chương>.<mục>.<tiểu mục>`.
- Hình/Bảng/Công thức dùng 2 cấp: `<chương>.<số thứ tự trong chương>`.
- Chú giải bảng đặt phía trên bảng; chú giải hình đặt dưới hình.
- Trích dẫn tài liệu trong nội dung theo dạng số trong ngoặc vuông `[x]`.
- Tài liệu tham khảo phải là tài liệu đã đọc và có trích dẫn trong nội dung.
- Đánh số trang liên tục từ Mở đầu đến hết Phụ lục.

## 5. Checklist triển khai LaTeX
- [ ] Có đầy đủ front matter theo mẫu khoa.
- [ ] Mở đầu/Kết luận không đánh số chương.
- [ ] 4 chương nội dung có mục tiêu đúng vai trò.
- [ ] Chỉ số mục không vượt 3 cấp.
- [ ] Chỉ số hình/bảng/công thức theo `<chương>.<thứ tự>`.
- [ ] Có nhận xét kết quả sau mỗi bảng kết quả quan trọng.
- [ ] Mọi tài liệu tham khảo đều có xuất hiện trong nội dung.

## 6. Dấu vết trích xuất
Dòng gốc nhận diện được từ file bố cục (rút gọn, phục vụ kiểm chứng):
- Khóa luận như một bài văn gồm có ba phần là Mở đầu, Các chương Nội dung,Kết luận Mở đầu và Kết luận không là chương nên không đánh chỉ số; Trong luận án Tiến sỹ ở nước ngoài Phần…
- Tài liệu tham khảo
- Phụ lục (nếu có) như đoạn mã chương trình v.v.
- 2. Tài liệu tham khảo
- Tài liệu tham khảo (TLTK)) và trích dẫn TLTK là một phần rất quan trọng trong khóa luận
- Mọi tài liệu tham khảo có trong danh mục tài liệu tham khảo ở cuối khóa luận
- Khi bố cục từng mục trong các chương của khóa luận, cần ánh xạ mỗi mục đó sử dụng nội dung các tài liệu tham khảo nào.
- Chương 1 sử dụng nhiều tài liệu tham khảo nhất
- Chương 2 sử dụng các tài liệu tham khảo liên quan trực tiếp tới 2-4 mô hình, kỹ thuật tiên tiến giải quyết bài toán của các tác giả khác.
- Như vậy chương 2 sử dụng vài ba tài liệu tham khảo; đây là các tài liệu tham khảo cập nhật.
- Chương này cũng chri dẫn ít tài liệu tham khảo, chủ yếu là như ở Chương 2.
- Trích dẫn tài liệu tham khảo
- - Khi chỉ dẫn tác giả tài liệu tham khảo thì làm như thầy đã hướng dẫn:
- - Hình vẽ lấy ở tài liệu tham khảo nào thì cần chỉ dẫn tài liệu tham khảo đó,
- - Tài liệu tham khảo phải đầy đủ thông tin.
- - Dùng không quá ba chỉ số mục: <chỉ số chương>.<chỉ số mục>.< chỉ số mục con>
- - Chí số hình, bảng, công thức: hai chỉ số <chỉ số chương>.<số thứ tự trong chương>
- - Trang bìa (xem Phụ lục 01).
- - Trang phụ bìa (xem Phụ lục 02).
- - Trang Lời cam đoan không sao chép các tài liệu, công trình nghiên cứu của người khác mà không chỉ rõ trong tài liệu tham khảo (khoảng 5-10 dòng).
