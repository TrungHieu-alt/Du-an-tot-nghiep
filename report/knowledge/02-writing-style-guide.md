# Writing Style Guide (Academic Vietnamese)

## Mục lục nội bộ
- [1. Mục tiêu giọng viết](#1-mục-tiêu-giọng-viết)
- [2. Chuẩn viết theo từng chương](#2-chuẩn-viết-theo-từng-chương)
- [3. Quy tắc trích dẫn và tham khảo](#3-quy-tắc-trích-dẫn-và-tham-khảo)
- [4. Quy tắc hình/bảng và nhận xét kết quả](#4-quy-tắc-hìnhbảng-và-nhận-xét-kết-quả)
- [5. Lỗi cần tránh](#5-lỗi-cần-tránh)
- [6. Cues tái sử dụng từ báo cáo cũ](#6-cues-tái-sử-dụng-từ-báo-cáo-cũ)

## 1. Mục tiêu giọng viết
- Giọng học thuật tiếng Việt chuẩn: khách quan, rõ luận điểm, có dẫn chứng.
- Ưu tiên mạch lập luận: bối cảnh -> vấn đề -> phương pháp -> kết quả -> bàn luận.
- Tránh văn phong quảng bá hoặc mô tả cảm tính không kiểm chứng.

## 2. Chuẩn viết theo từng chương
- Chương 1:
  - Giải thích bối cảnh, phát biểu bài toán rõ input/output, mục tiêu và phạm vi.
  - Tổng hợp related work để làm nền cho khoảng trống nghiên cứu.
- Chương 2:
  - Trình bày 2-4 kỹ thuật/mô hình tiên tiến liên quan trực tiếp.
  - Nêu điểm mạnh/yếu và lý do chọn tổ hợp kỹ thuật cho đề tài.
- Chương 3:
  - Trình bày mô hình đề xuất, kiến trúc thành phần và luồng xử lý.
  - Làm rõ điểm sáng tạo so với cách tiếp cận có sẵn.
- Chương 4:
  - Nêu thiết lập thực nghiệm, dữ liệu, công cụ, độ đo, kịch bản.
  - Không chỉ đưa bảng số liệu; bắt buộc có nhận xét, phân tích và liên hệ công trình liên quan.
- Kết luận:
  - Tóm tắt kết quả đạt được, hạn chế kỹ thuật/dữ liệu, hướng phát triển tiếp theo.

## 3. Quy tắc trích dẫn và tham khảo
- Citation style mặc định: numeric bracket `[x]`.
- Cách dẫn tác giả trong câu:
  - Một tác giả: `A [x]`.
  - Hai tác giả: `A và B [x]`.
  - Từ ba tác giả: `A và cộng sự [x]`.
- Danh mục tài liệu tham khảo:
  - Chỉ liệt kê tài liệu đã đọc và có dùng trong nội dung.
  - Mỗi mục phải đủ thông tin (tác giả, tiêu đề, nguồn, năm, trang).
  - Có thể phân nhóm theo ngôn ngữ và sắp xếp theo ABC theo quy định.

## 4. Quy tắc hình/bảng và nhận xét kết quả
- Caption bảng đặt trên bảng; caption hình đặt dưới hình.
- Đánh số theo chương: `Hình 2.1`, `Bảng 4.3`, ...
- Mỗi bảng kết quả chính cần có đoạn nhận xét:
  - Xu hướng số liệu.
  - So sánh baseline hoặc công trình liên quan (nếu có).
  - Giải thích nguyên nhân khi kết quả chưa tốt.

## 5. Lỗi cần tránh
- Để tiêu đề/chú thích tiếng Anh khi phần nội dung đang chuẩn hóa tiếng Việt.
- Chỉ liệt kê kết quả mà thiếu phân tích.
- Citation không nhất quán (lúc `[x]`, lúc tác giả-năm).
- Chương 3 trùng lặp chương 2, không nêu điểm mới.
- Chương 1 thiếu phát biểu bài toán cụ thể.

## 6. Cues tái sử dụng từ báo cáo cũ
Gợi ý các cụm mục con có thể tái dùng làm hạt giống khi viết lại (không copy nguyên văn):
- Thách thức của quy trình tuyển dụng hiện đại
- Những hạn chế kỹ thuật cụ thể
- Cơ hội từ kiến trúc RAG
- Mục tiêu tổng quát
- Mục tiêu cụ thể
- Kiến trúc Retrieval-Augmented Generation (RAG)
- Biểu diễn thực thể bằng vector (Embedding)
- Nhận dạng, chuẩn hóa và liên kết thực thể
- Mô hình ngôn ngữ nhỏ và mô hình ngôn ngữ lớn (SLM và LLM)
- Đa tác tử (Multi-agent)
- Knowledge Graph (KG)
- Mục đích
- Quy trình tiền xử lý
- Embedding models
- Skills Embedding Model
- Job-CV Context Embedding
- Vai trò của Knowledge Graph trong hệ thống
- Thiết kế các Knowledge Graph
- Xây dựng Knowledge Graph
- Chấm điểm dựa trên Knowledge Graph

Mục chi tiết sâu có thể đẩy xuống tiểu mục kỹ thuật:
- 3.3.3.1. Triển khai và môi trường chạy
- 3.3.3.2 Chi tiết triển khai và giao diện người dùng
- 3.4.1.1. Kiểu đầu vào và trích xuất văn bản
- 3.4.1.2. Nhận diện ngôn ngữ và dịch
- 3.4.1.3. Parsing CV/JD sang JSON
- 3.4.1.4. Phân tích độ trễ và chi phí của bước parsing
- 3.4.2.1. Lựa chọn embedding model
- 3.4.2.2. Chiến lược embedding đa trường
- 3.4.2.3. Lưu trữ vector trong ChromaDB
- 3.4.3.1. Stage 1 – ANN Retrieval (Top-50)
- 3.4.3.2. Stage 2 – Weighted Field Reranking (Top-10)
- 3.4.3.3. Stage 3 – LLM Evaluation & Hybrid Score (Top-5)

Dấu vết trích xuất về citation/rule (rút gọn):
- + Một tác giả A thì viết "A[x]",
- + Hai tác giả A và B thì viết "A và B [x]",
- + Từ ba tác giả trở lên A, B, C ... thì viết "A và cộng sự [x]".
- - Không để chú thích tiếng Anh ở đề mục,
- - Tài liệu tham khảo phải đầy đủ thông tin.
- 3. Các tài liệu tham khảo khi liệt kê vào danh mục phải đầy đủ các thông tin cần thiết và theo trình tự sau: Số thứ tự (đặt trong cặp dấu ngoặc vuông), Họ tên tác giả, Tên tài liệ…
- 7. Tài liệu tham khảo trích dẫn trong KLTN được ghi theo số thứ tự của tài liệu tham khảo ở Danh mục tài liệu tham khảo này của KLTN và số thứ tự đó được đặt trong cặp dấu ngoặc v…
