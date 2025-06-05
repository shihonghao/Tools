import os
import sys
import tempfile
import zipfile
from pathlib import Path
from pdf2image import convert_from_path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.patch_stdout import patch_stdout

def input_path_with_completion(prompt_text):
    session = PromptSession(completer=PathCompleter(expanduser=True))
    try:
        with patch_stdout():
            return session.prompt(prompt_text).strip()
    except KeyboardInterrupt:
        print("\n⏹ 输入中断，程序退出。")
        sys.exit(0)

def convert_pdf_to_cbz_interactive():
    try:
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
            success_count = 0
            for i, pdf in enumerate(pdfs, start=1):
                rel = pdf.relative_to(pdf_input).with_suffix('.cbz')
                out_cbz = output_path / rel
                print(f"\n[{i}/{len(pdfs)}] 处理：{pdf}")
                try:
                    _convert_single(pdf, out_cbz, image_format, dpi)
                    success_count += 1
                except Exception as e:
                    print(f"❌ 转换失败：{pdf}\n原因：{e}")
            print(f"\n✅ 完成 {success_count}/{len(pdfs)} 个 PDF 转换")

        else:
            print("❌ 输入路径无效。")

    except KeyboardInterrupt:
        print("\n⏹ 用户中断，程序退出。")
        sys.exit(0)

def _convert_single(pdf_path, cbz_path, image_format, dpi):
    print(f"➡️ 开始转换: {pdf_path}")
    with tempfile.TemporaryDirectory() as tmp_dir:
        images = convert_from_path(str(pdf_path), dpi=dpi)
        for i, img in enumerate(images):
            print(f"🖼 处理第 {i+1}/{len(images)} 页...", end="\r")
            img_path = os.path.join(tmp_dir, f"page_{i:03}.{image_format}")
            if image_format == 'jpg':
                img = img.convert('RGB')
            img.save(img_path)
        cbz_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(cbz_path, 'w') as cbz:
            for img_file in sorted(os.listdir(tmp_dir)):
                cbz.write(os.path.join(tmp_dir, img_file), arcname=img_file)
    print(f"✅ 成功保存 CBZ：{cbz_path}")

def main():
    try:
        while True:
            print("\n====== 工具包菜单 ======")
            print("1. PDF 转 CBZ")
            print("0. 退出")
            choice = input("请选择操作：").strip()
            if choice == '1':
                convert_pdf_to_cbz_interactive()
            elif choice == '0':
                print("退出程序。")
                break
            else:
                print("无效选择，请重试。")
    except KeyboardInterrupt:
        print("\n⏹ 用户中断，程序退出。")
        sys.exit(0)

if __name__ == "__main__":
    main()
