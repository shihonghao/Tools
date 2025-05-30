import os
import tempfile
import zipfile
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter

def input_path_with_completion(prompt_text):
    completer = PathCompleter(expanduser=True)
    return prompt(prompt_text, completer=completer).strip()

def convert_pdf_to_cbz_interactive():
    print("\n📘 PDF 转 CBZ 工具")
    pdf_input = input_path_with_completion("📂 输入 PDF 文件路径或目录：")
    output_path = input_path_with_completion("📁 输出 CBZ 文件或目录路径：")
    image_format = input("🖼 图像格式 [png/jpg]（默认 png）：").strip().lower() or "png"
    dpi_input = input("🔍 图像 DPI（默认 300）：").strip()
    try:
        dpi = int(dpi_input) if dpi_input else 300
    except ValueError:
        dpi = 300

    pdf_input = Path(pdf_input)
    output_path = Path(output_path)

    if pdf_input.is_file():
        if output_path.is_dir():
            out_cbz = output_path / pdf_input.with_suffix('.cbz').name
        else:
            out_cbz = output_path
        _convert_single(pdf_input, out_cbz, image_format, dpi)

    elif pdf_input.is_dir():
        pdfs = list(pdf_input.rglob("*.pdf"))
        if not pdfs:
            print("⚠️ 没有找到 PDF 文件。")
            return
        for pdf in pdfs:
            rel = pdf.relative_to(pdf_input).with_suffix('.cbz')
            out_cbz = output_path / rel
            _convert_single(pdf, out_cbz, image_format, dpi)
        print(f"\n✅ 完成 {len(pdfs)} 个 PDF 转换")

    else:
        print("❌ 输入路径无效。")

def _convert_single(pdf_path, cbz_path, image_format, dpi):
    print(f"➡️ 转换: {pdf_path} → {cbz_path}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        images = convert_from_path(str(pdf_path), dpi=dpi)
        for i, img in enumerate(images):
            img_path = os.path.join(tmp_dir, f"page_{i:03}.{image_format}")
            if image_format == 'jpg':
                img = img.convert('RGB')
            img.save(img_path)
        cbz_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(cbz_path, 'w') as cbz:
            for img_file in sorted(os.listdir(tmp_dir)):
                cbz.write(os.path.join(tmp_dir, img_file), arcname=img_file)
