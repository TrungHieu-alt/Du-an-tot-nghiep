# Knowledge Pack Usage Rules

## Mục lục nội bộ
- [1. Mục tiêu](#1-mục-tiêu)
- [2. Phạm vi và ưu tiên nguồn](#2-phạm-vi-và-ưu-tiên-nguồn)
- [3. Quy trình chuẩn khi viết LaTeX](#3-quy-trình-chuẩn-khi-viết-latex)
- [4. Rule theo loại tác vụ viết](#4-rule-theo-loại-tác-vụ-viết)
- [5. Rule về trích dẫn và tái sử dụng nội dung](#5-rule-về-trích-dẫn-và-tái-sử-dụng-nội-dung)
- [6. Khi nào được mở lại file DOCX gốc](#6-khi-nào-được-mở-lại-file-docx-gốc)
- [7. Checklist chất lượng trước khi chốt section](#7-checklist-chất-lượng-trước-khi-chốt-section)
- [8. Lệnh tái tạo knowledge pack](#8-lệnh-tái-tạo-knowledge-pack)
- [9. Mẫu dùng nhanh](#9-mẫu-dùng-nhanh)

## 1. Mục tiêu
Tài liệu này chuẩn hóa cách sử dụng bộ Knowledge Pack để viết báo cáo LaTeX nhanh, nhất quán và không phải đọc lại hai file DOCX lớn mỗi lần.

## 2. Phạm vi và ưu tiên nguồn
Nguồn sử dụng theo thứ tự ưu tiên bắt buộc:
1. `01-structure-blueprint.md`: source-of-truth về bố cục và khung chương mục.
2. `02-writing-style-guide.md`: source-of-truth về giọng viết, citation, cách phân tích kết quả.
3. `03-legacy-content-map.md`: nguồn ý và luận điểm tái sử dụng từ báo cáo cũ.

Rule ưu tiên:
- Nếu `03` mâu thuẫn `01`: luôn theo `01`.
- Nếu nội dung đúng cấu trúc nhưng sai văn phong: sửa theo `02`.
- `03` chỉ cung cấp ý, không ép copy nguyên văn.

## 3. Quy trình chuẩn khi viết LaTeX
Áp dụng cho mọi section/chương:
1. Xác định mục tiêu section cần viết (ví dụ `3.2 Thiết kế mô hình`).
2. Mở `01` để lấy vị trí section trong khung bắt buộc.
3. Mở `02` để lấy rule giọng viết và yêu cầu nội dung của chương tương ứng.
4. Mở `03` để lấy content blocks và heading gợi ý.
5. Soạn bản nháp theo mẫu:
   - Câu mở bối cảnh/mục tiêu.
   - Thân đoạn mô tả phương pháp/kết quả.
   - Câu kết nối sang mục kế tiếp hoặc nêu kết luận ngắn.
6. Chèn citation `[x]` ngay khi viết, không để dồn cuối.
7. Chạy checklist ở Mục 7 trước khi chốt.

## 4. Rule theo loại tác vụ viết
### 4.1 Viết khung chương/mục
- Chỉ lấy từ `01`.
- Không suy diễn thêm chương thứ 5 nếu không có yêu cầu chính thức.

### 4.2 Viết nội dung học thuật
- Dùng `02` để kiểm soát giọng văn và độ chặt luận điểm.
- Dùng `03` để lấy ý chính và thứ tự logic.

### 4.3 Viết thực nghiệm và đánh giá
- Bắt buộc có đoạn nhận xét cho bảng kết quả (không chỉ nêu số).
- Nêu rõ độ đo, baseline/đối chiếu, và nguyên nhân khi kết quả chưa tốt.

### 4.4 Viết kết luận
- Phải có đủ 3 phần: kết quả đạt được, hạn chế, hướng phát triển.

## 5. Rule về trích dẫn và tái sử dụng nội dung
- Style trích dẫn mặc định: numeric bracket `[x]`.
- Cách dẫn tác giả trong câu theo `02`:
  - `A [x]`, `A và B [x]`, `A và cộng sự [x]`.
- Không copy dài nguyên văn từ báo cáo cũ; ưu tiên diễn đạt lại cùng luận điểm.
- Không tạo claim học thuật mới nếu không có chỗ dựa từ nội dung hiện có.

## 6. Khi nào được mở lại file DOCX gốc
Chỉ mở lại DOCX khi có ít nhất một điều kiện:
1. Knowledge Pack thiếu mục cần thiết cho section đang viết.
2. Cần kiểm tra chi tiết visual/layout mà markdown không giữ được.
3. Cần xác minh nguyên văn một câu trích dẫn đặc biệt.

Nếu không thuộc 3 trường hợp trên: không mở lại DOCX, dùng Knowledge Pack.

## 7. Checklist chất lượng trước khi chốt section
- [ ] Section đúng vị trí trong khung `01`.
- [ ] Nội dung đúng mục tiêu chương theo `02`.
- [ ] Có dùng ý từ `03` nhưng đã diễn đạt lại.
- [ ] Có citation `[x]` cho các luận điểm cần nguồn.
- [ ] Không trộn tiếng Anh vào tiêu đề/chú thích nếu không cần thiết.
- [ ] Với phần kết quả: có nhận xét, không chỉ liệt kê bảng số liệu.

## 8. Lệnh tái tạo knowledge pack
Khi file DOCX nguồn thay đổi, chạy lại:

```bash
python3 report/tools/extract_docx_knowledge.py \
  --layout report/Bo-cuc-khoa-luan.docx \
  --legacy "report/Dự án khoa học.docx" \
  --out report/knowledge
```

Sau khi regenerate:
- Rà lại `01/02/03`.
- Giữ `04-usage-rules.md` làm policy cố định (chỉ update khi workflow đổi).

## 9. Mẫu dùng nhanh
Mẫu yêu cầu viết 1 section (dùng cho AI hoặc tự viết):

```text
Viết mục <chapter.section title> theo rule trong:
- report/knowledge/01-structure-blueprint.md
- report/knowledge/02-writing-style-guide.md
- report/knowledge/03-legacy-content-map.md

Ràng buộc:
- Giọng học thuật tiếng Việt.
- Không copy nguyên văn dài từ báo cáo cũ.
- Chèn citation [x] tại các luận điểm chính.
- Kết thúc bằng 2-3 câu chuyển tiếp sang mục kế.
```

Mẫu tự kiểm trước khi chốt:

```text
1) Có bám đúng khung chương của 01 chưa?
2) Có đúng giọng viết và mục tiêu chương theo 02 chưa?
3) Ý tái dùng từ 03 đã được diễn đạt lại chưa?
4) Citation [x] đã đủ chưa?
5) Nếu là phần thực nghiệm: đã có nhận xét sau bảng chưa?
```

## 10. Visual Style Lock (Chuẩn đã chốt)
Áp dụng cho toàn bộ báo cáo LaTeX hiện tại, trừ khi người dùng yêu cầu đổi lại.

- Font toàn cục: TeX Gyre Termes (Times-style) cho nội dung văn bản.
- Heading: màu đen 100% ở mọi cấp.
- Phân cấp heading: Chapter lớn hơn Section, Section lớn hơn Subsection.
- Thuật ngữ tiếng Anh: giữ nguyên khi cần, nhưng không dùng kiểu chữ “code-style”.
- List of Tables: dùng định dạng đồng nhất cho toàn bộ dòng (cùng indent, prefix, khoảng cách dòng đều nhau).
- Phụ lục và thân bài: ưu tiên mô tả mô hình xử lý nghiệp vụ, không trình bày theo địa chỉ source code hay tên biến/bảng kỹ thuật.

Khi cập nhật báo cáo:
1) Không tự ý đổi khỏi chuẩn trên.
2) Nếu cần đổi visual style, phải ghi rõ lý do và cập nhật lại mục này ngay trong cùng task.
