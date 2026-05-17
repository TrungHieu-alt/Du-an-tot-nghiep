#!/usr/bin/env python3
"""Extract reusable knowledge pack from two DOCX sources.

Usage:
  python3 report/tools/extract_docx_knowledge.py \
    --layout report/Bo-cuc-khoa-luan.docx \
    --legacy "report/Dự án khoa học.docx" \
    --out report/knowledge
"""

from __future__ import annotations

import argparse
import os
import re
import textwrap
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass
class Paragraph:
    style: str
    text: str


def read_docx_paragraphs(docx_path: Path) -> list[Paragraph]:
    with zipfile.ZipFile(docx_path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    out: list[Paragraph] = []
    for p in root.findall(".//w:body/w:p", NS):
        text = "".join(t.text or "" for t in p.findall(".//w:t", NS)).strip()
        if not text:
            continue
        style = "Normal"
        ppr = p.find("w:pPr", NS)
        if ppr is not None:
            pstyle = ppr.find("w:pStyle", NS)
            if pstyle is not None:
                style = pstyle.attrib.get(f"{{{NS['w']}}}val", "Normal")
        out.append(Paragraph(style=style, text=text))
    return out


def headings(paragraphs: Iterable[Paragraph]) -> list[Paragraph]:
    return [p for p in paragraphs if p.style.startswith("Heading")]


def find_lines(paragraphs: Iterable[Paragraph], patterns: list[str]) -> list[str]:
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    lines: list[str] = []
    for p in paragraphs:
        text = p.text.strip()
        for regex in compiled:
            if regex.search(text):
                lines.append(text)
                break
    return dedup(lines)


def dedup(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip()
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def short(text: str, limit: int = 180) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= limit else t[: limit - 1].rstrip() + "…"


def normalize_markdown_block(text: str) -> str:
    lines = text.splitlines()
    cleaned = [line[8:] if line.startswith("        ") else line for line in lines]
    return "\n".join(cleaned).strip() + "\n"


def chapter_from_heading_h1(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["giới thiệu", "co sở", "cơ sở lý thuyết"]):
        return "Chương 1"
    if any(k in t for k in ["phân tích", "thiết kế", "mô hình"]):
        return "Chương 2/3"
    if any(k in t for k in ["cài đặt", "thực nghiệm", "validation", "results"]):
        return "Chương 4"
    if "kết luận" in t:
        return "Kết luận"
    return "Khác"


def build_structure_blueprint(layout_paras: list[Paragraph]) -> str:
    layout_rules = find_lines(
        layout_paras,
        patterns=[
            r"mở đầu.*không.*chương",
            r"không đánh thứ tự",
            r"dùng không quá ba chỉ số mục",
            r"chí số hình|chỉ số hình|chú giải",
            r"tài liệu tham khảo",
            r"phụ lục",
            r"lề trên|lề dưới|lề trái|lề phải",
            r"cỡ chữ|dãn dòng|font",
            r"số trang",
        ],
    )

    content = textwrap.dedent(
        f"""\
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
        {os.linesep.join(f"- {short(line)}" for line in layout_rules[:20]) if layout_rules else "- (không nhận diện được rule cụ thể bằng regex)"}
        """
    )
    return normalize_markdown_block(content)


def build_writing_style_guide(layout_paras: list[Paragraph], legacy_paras: list[Paragraph]) -> str:
    citation_lines = find_lines(
        layout_paras,
        patterns=[
            r"một tác giả",
            r"hai tác giả",
            r"ba tác giả",
            r"ngoặc vuông",
            r"không để chú thích tiếng anh",
            r"tài liệu tham khảo phải đầy đủ",
        ],
    )

    legacy_h3 = [p.text for p in headings(legacy_paras) if p.style == "Heading3"]
    legacy_h4 = [p.text for p in headings(legacy_paras) if p.style == "Heading4"]

    content = textwrap.dedent(
        f"""\
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
        {os.linesep.join(f"- {short(x)}" for x in legacy_h3[:20]) if legacy_h3 else "- (không có Heading3)"}

        Mục chi tiết sâu có thể đẩy xuống tiểu mục kỹ thuật:
        {os.linesep.join(f"- {short(x)}" for x in legacy_h4[:12]) if legacy_h4 else "- (không có Heading4)"}

        Dấu vết trích xuất về citation/rule (rút gọn):
        {os.linesep.join(f"- {short(line)}" for line in citation_lines[:12]) if citation_lines else "- (không nhận diện thêm rule citation bằng regex)"}
        """
    )
    return normalize_markdown_block(content)


def build_legacy_content_map(legacy_paras: list[Paragraph]) -> str:
    h1_sections: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for p in legacy_paras:
        if p.style == "Heading1":
            current = {"h1": p.text, "h2": [], "h3": [], "samples": []}
            h1_sections.append(current)
            continue
        if current is None:
            continue
        if p.style == "Heading2":
            cast_list = current["h2"]
            assert isinstance(cast_list, list)
            cast_list.append(p.text)
        elif p.style == "Heading3":
            cast_list = current["h3"]
            assert isinstance(cast_list, list)
            cast_list.append(p.text)
        elif p.style in {"Normal", "ListParagraph"} and len(p.text) > 80:
            cast_list = current["samples"]
            assert isinstance(cast_list, list)
            if len(cast_list) < 4:
                cast_list.append(short(p.text, 220))

    filtered = [
        s
        for s in h1_sections
        if str(s["h1"]).lower()
        not in {"table of figures", "table of tables", "lời cam đoan", "lời cảm ơn", "tài liệu tham khảo"}
    ]

    lines: list[str] = []
    lines.append("# Legacy Content Map (Old Report -> New Structure)")
    lines.append("")
    lines.append("## Mục lục nội bộ")
    lines.append("- [1. Mục tiêu mapping](#1-mục-tiêu-mapping)")
    lines.append("- [2. Mapping theo chương mới](#2-mapping-theo-chương-mới)")
    lines.append("- [3. Section map chi tiết từ báo cáo cũ](#3-section-map-chi-tiết-từ-báo-cáo-cũ)")
    lines.append("- [4. Reusable content blocks](#4-reusable-content-blocks)")
    lines.append("- [5. Spot-check heading](#5-spot-check-heading)")
    lines.append("")
    lines.append("## 1. Mục tiêu mapping")
    lines.append(
        "Tài liệu này ánh xạ cấu trúc và ý chính của báo cáo cũ sang bố cục 4 chương mới để tái sử dụng nhanh khi viết LaTeX."
    )
    lines.append("Nguyên tắc: tái sử dụng ý và luận điểm, không copy dài nguyên văn.")
    lines.append("")
    lines.append("## 2. Mapping theo chương mới")
    lines.append("- Chương 1 (Giới thiệu + cơ sở): dùng các phần bối cảnh, vấn đề, mục tiêu, related work, cơ sở lý thuyết.")
    lines.append("- Chương 2 (Kỹ thuật tiên tiến): dùng các phần embedding, KG, retrieval/reranking, location xử lý như nền kỹ thuật.")
    lines.append("- Chương 3 (Mô hình đề xuất): dùng kiến trúc hệ thống + pipeline đề xuất + chiến lược multi-agent cụ thể của đề tài.")
    lines.append("- Chương 4 (Thực nghiệm/đánh giá): dùng phần cài đặt thực nghiệm, testing/validation, kết quả và phân tích hiệu năng.")
    lines.append("- Kết luận: dùng phần hạn chế và hướng phát triển.")
    lines.append("")
    lines.append("## 3. Section map chi tiết từ báo cáo cũ")
    for sec in filtered:
        h1 = str(sec["h1"])
        lines.append(f"### {h1}")
        lines.append(f"- Gợi ý chương đích: {chapter_from_heading_h1(h1)}")
        h2 = sec["h2"]
        h3 = sec["h3"]
        samples = sec["samples"]
        assert isinstance(h2, list) and isinstance(h3, list) and isinstance(samples, list)
        if h2:
            lines.append("- Mục cấp 2:")
            for item in h2[:12]:
                lines.append(f"  - {short(str(item), 150)}")
        if h3:
            lines.append("- Mục cấp 3 tiêu biểu:")
            for item in h3[:14]:
                lines.append(f"  - {short(str(item), 150)}")
        if samples:
            lines.append("- Ý chính có thể tái dùng:")
            for item in samples[:4]:
                lines.append(f"  - {short(str(item), 170)}")
        lines.append("")

    lines.append("## 4. Reusable content blocks")
    lines.append("- Problem framing: thách thức tuyển dụng hiện đại, dữ liệu phi cấu trúc CV/JD.")
    lines.append("- Technical pipeline: preprocessing -> embedding -> KG augmentation -> retrieval -> reranking/reasoning.")
    lines.append("- System design: kiến trúc nhiều tầng, module hóa theo chức năng.")
    lines.append("- Experiment design: tập dữ liệu, kịch bản, độ đo, baseline so sánh.")
    lines.append("- Result discussion: phân tích xu hướng, nguyên nhân, hạn chế và hướng phát triển.")
    lines.append("")
    lines.append("## 5. Spot-check heading")
    lines.append("10 heading lấy từ báo cáo cũ để đối chiếu nhanh:")
    sampled = []
    for sec in filtered:
        h3 = sec["h3"]
        assert isinstance(h3, list)
        for x in h3:
            sampled.append(str(x))
    for item in sampled[:10]:
        lines.append(f"- {short(item, 180)}")

    return "\n".join(lines) + "\n"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract docx knowledge pack.")
    parser.add_argument("--layout", required=True, type=Path, help="Path to layout/guideline docx.")
    parser.add_argument("--legacy", required=True, type=Path, help="Path to legacy report docx.")
    parser.add_argument("--out", required=True, type=Path, help="Output directory (e.g., report/knowledge).")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    layout_paras = read_docx_paragraphs(args.layout)
    legacy_paras = read_docx_paragraphs(args.legacy)

    f1 = args.out / "01-structure-blueprint.md"
    f2 = args.out / "02-writing-style-guide.md"
    f3 = args.out / "03-legacy-content-map.md"

    write_file(f1, build_structure_blueprint(layout_paras))
    write_file(f2, build_writing_style_guide(layout_paras, legacy_paras))
    write_file(f3, build_legacy_content_map(legacy_paras))

    print("Generated:")
    print(f"- {f1}")
    print(f"- {f2}")
    print(f"- {f3}")


if __name__ == "__main__":
    main()
