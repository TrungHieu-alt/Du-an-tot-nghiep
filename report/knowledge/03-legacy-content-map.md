# Legacy Content Map (Old Report -> New Structure)

## Mục lục nội bộ
- [1. Mục tiêu mapping](#1-mục-tiêu-mapping)
- [2. Mapping theo chương mới](#2-mapping-theo-chương-mới)
- [3. Section map chi tiết từ báo cáo cũ](#3-section-map-chi-tiết-từ-báo-cáo-cũ)
- [4. Reusable content blocks](#4-reusable-content-blocks)
- [5. Spot-check heading](#5-spot-check-heading)

## 1. Mục tiêu mapping
Tài liệu này ánh xạ cấu trúc và ý chính của báo cáo cũ sang bố cục 4 chương mới để tái sử dụng nhanh khi viết LaTeX.
Nguyên tắc: tái sử dụng ý và luận điểm, không copy dài nguyên văn.

## 2. Mapping theo chương mới
- Chương 1 (Giới thiệu + cơ sở): dùng các phần bối cảnh, vấn đề, mục tiêu, related work, cơ sở lý thuyết.
- Chương 2 (Kỹ thuật tiên tiến): dùng các phần embedding, KG, retrieval/reranking, location xử lý như nền kỹ thuật.
- Chương 3 (Mô hình đề xuất): dùng kiến trúc hệ thống + pipeline đề xuất + chiến lược multi-agent cụ thể của đề tài.
- Chương 4 (Thực nghiệm/đánh giá): dùng phần cài đặt thực nghiệm, testing/validation, kết quả và phân tích hiệu năng.
- Kết luận: dùng phần hạn chế và hướng phát triển.

## 3. Section map chi tiết từ báo cáo cũ
### Giới thiệu và cơ sở lý thuyết
- Gợi ý chương đích: Chương 1
- Mục cấp 2:
  - Vấn đề
  - Mục tiêu dự án
  - Related work
  - Cơ sở lý thuyết
- Mục cấp 3 tiêu biểu:
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
- Ý chính có thể tái dùng:
  - Trong bối cảnh chuyển đổi số mạnh mẽ hiện nay, hoạt động tuyển dụng nhân sự đang đối mặt với nhiều thách thức, đặc biệt tại các doanh nghiệp có quy mô vừa và lớn. Số lượ…
  - Các phương pháp tuyển dụng truyền thống, dựa nhiều vào xử lý thủ công hoặc các hệ thống quản lý hồ sơ đơn giản, thường gặp phải các vấn đề như tốn nhiều thời gian, thiếu…
  - Văn bản dài và phi cấu trúc: CV (resume) và tin tuyển dụng (job description) thường là các tài liệu dài, phức tạp, không có ranh giới trường dữ liệu rõ ràng. Dữ liệu tro…
  - Hạn chế của tìm kiếm từ khóa: Các hệ thống truyền thống chỉ hỗ trợ tìm kiếm theo từ khóa hoặc bộ lọc cố định, dẫn đến khả năng khai thác thông tin còn hạn chế. Các phươn…

### Phân tích & Thiết kế Mô hình
- Gợi ý chương đích: Chương 2/3
- Mục cấp 2:
  - Tổng quan kiến trúc hệ thống
  - Tiền xử lí dữ liệu
  - Embedding
  - Kết hợp Knowledge Graph
  - Xử lí location
  - Retrieval
  - Reranking và sinh kết quả bằng LLM Agent
  - Chiến lược phát triển Multi-Agent System
- Mục cấp 3 tiêu biểu:
  - Mục đích
  - Quy trình tiền xử lý
  - Embedding models
  - Skills Embedding Model
  - Job-CV Context Embedding
  - Vai trò của Knowledge Graph trong hệ thống
  - Thiết kế các Knowledge Graph
  - Xây dựng Knowledge Graph
  - Chấm điểm dựa trên Knowledge Graph
  - Phân cấp và tính khoảng cách
  - Quy tắc đánh giá điểm
  - Các điểm thành phần
  - Tính điểm kênh Skills
  - Tính điểm kênh Context
- Ý chính có thể tái dùng:
  - Hệ thống được thiết kế theo kiến trúc pipeline xử lý dữ liệu nhiều tầng, trong đó mỗi tầng đảm nhiệm một vai trò rõ ràng và có thể tối ưu độc lập. Mục tiêu tổng thể của…
  - Luồng xử lý bắt đầu từ dữ liệu văn bản thô (job description hoặc CV), đi qua các bước chuẩn hóa, biểu diễn ngữ nghĩa, bổ sung tri thức có cấu trúc và cuối cùng là suy lu…
  - Hình 2.1 minh họa kiến trúc tổng thể của hệ thống, trong đó toàn bộ quy trình xử lý được tổ chức theo dạng pipeline nhiều giai đoạn. Kiến trúc này nhằm giải quyết bài to…
  - Trong pipeline này, dữ liệu đầu vào được tiền xử lý và chuẩn hóa trước khi được ánh xạ sang không gian vector thông qua mô hình embedding. Song song với đó, tri thức miề…

### Cài đặt thực nghiệm
- Gợi ý chương đích: Chương 4
- Mục cấp 2:
  - Tổng Quan & Động Lực
  - Hệ Thống Overview & Architecture
  - System Design
  - RAG Matching Pipeline
  - Testing & Validation Approach
  - Results & Performance Analysis
  - Lưu ý về tài liệu bổ sung
- Mục cấp 3 tiêu biểu:
  - Mục tiêu chương
  - Phạm vi
  - Kiến trúc tổng quan
  - Data flow và cơ chế matching hai chiều
  - Tóm tắt công nghệ
  - Thiết kế cơ sở dữ liệu
  - Backend API và luồng xử lý
  - Kiến trúc frontend
  - Preprocessing & Parsing
  - Embedding & Vector Storage
  - Hybrid Retrieval & Scoring
  - LLM Evaluation & Reasoning
  - Data Persistence
  - Implementation vs Theory: Gaps Analysis
- Ý chính có thể tái dùng:
  - Mục tiêu của chương này là chuyển hóa kiến trúc Retrieval-Augmented Generation (RAG) đã trình bày ở Chương 2 thành một hệ thống chạy được trong thực tế, có khả năng xử l…
  - Bên cạnh việc mô tả triển khai, chương này cũng nhằm làm rõ khoảng cách giữa mô hình lý thuyết (Chương 2) và phiên bản prototype (cài đặt thực tế). Việc phân tích “gaps”…
  - Trong phạm vi đồ án, phần triển khai tập trung vào “core” của hệ thống RAG matching, bao gồm tiền xử lý, biểu diễn embedding, truy hồi, tái xếp hạng và chấm điểm bằng LL…
  - Hệ thống được xây dựng theo mô hình client–server tiêu chuẩn, trong đó frontend cung cấp hai giao diện sử dụng chính cho hai nhóm người dùng: ứng viên (candidate) và nhà…

### Kết luận và hướng phát triển
- Gợi ý chương đích: Kết luận
- Ý chính có thể tái dùng:
  - Mặc dù hệ thống đã đạt được mục tiêu xây dựng một pipeline RAG hoạt động end-to-end, phiên bản prototype vẫn tồn tại một số hạn chế về chất lượng matching, độ tin cậy và…

## 4. Reusable content blocks
- Problem framing: thách thức tuyển dụng hiện đại, dữ liệu phi cấu trúc CV/JD.
- Technical pipeline: preprocessing -> embedding -> KG augmentation -> retrieval -> reranking/reasoning.
- System design: kiến trúc nhiều tầng, module hóa theo chức năng.
- Experiment design: tập dữ liệu, kịch bản, độ đo, baseline so sánh.
- Result discussion: phân tích xu hướng, nguyên nhân, hạn chế và hướng phát triển.

## 5. Spot-check heading
10 heading lấy từ báo cáo cũ để đối chiếu nhanh:
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
