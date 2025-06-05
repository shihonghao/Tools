import os
import sys
import tempfile
import zipfile
import logging
from collections import Counter
from pathlib import Path
from pdf2image import convert_from_path
from pdf2image.pdf2image import pdfinfo_from_path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.patch_stdout import patch_stdout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
import fitz  # PyMuPDF 用于分析图像 DPI

# 批量转换 JPG 默认质量（1-95）
BATCH_JPG_QUALITY_DEFAULT = 75

# 设置日志（仅输出到控制台）
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def input_path_with_completion(prompt_text):
    session = PromptSession(completer=PathCompleter(expanduser=True))
    try:
        with patch_stdout():
            return session.prompt(prompt_text).strip()
    except KeyboardInterrupt:
        print("\n⏹ 输入中断，程序退出。")
        sys.exit(0)

def analyze_pdf_recommended_dpi(pdf_path, target_width_inch=8):
    """
    通过统计所有图片的推荐 DPI，返回出现频率最高的 DPI 作为整体推荐 DPI。
    """
    try:
        logger.info(f"自动推荐 DPI 分析中：{pdf_path}")
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        logger.warning(f"⚠️ 无法打开 PDF 分析 DPI：{e}")
        return 300

    dpi_counter = Counter()
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        images = page.get_images(full=True)
        if not images:
            # 如果该页没有图片，默认推荐 72 DPI
            dpi_counter[72] += 1
        for img in images:
            xref = img[0]
            base_image = doc.extract_image(xref)
            width = base_image["width"]
            recommended_dpi = round(width / target_width_inch)
            dpi_counter[recommended_dpi] += 1
        logger.info(f"页面 {page_num+1} 推荐 DPI 计数: {dict(dpi_counter)}")

    if not dpi_counter:
        overall_dpi = 300
    else:
        # 返回出现次数最多的 dpi
        overall_dpi = dpi_counter.most_common(1)[0][0]
    logger.info(f"{pdf_path} 的整体推荐 DPI（出现频率最高）：{overall_dpi}")
    return overall_dpi

def convert_pdf_to_cbz_interactive():
    try:
        print("\n📘 PDF 转 CBZ 工具")
        pdf_input = input_path_with_completion("📂 输入 PDF 文件路径或目录：")
        output_path = input_path_with_completion("📁 输出 CBZ 文件或目录路径：")
        image_format = input("🖼 图像格式 [png/jpg]（默认 png）：").strip().lower() or "png"
        dpi_input = input("🔍 图像 DPI（填 auto 或数字，默认 auto）：").strip().lower()

        pdf_input = Path(pdf_input)
        output_path = Path(output_path)

        if dpi_input == "auto" or dpi_input == "":
            dpi = None
        else:
            try:
                dpi = int(dpi_input)
            except ValueError:
                dpi = 300

        if pdf_input.is_file():
            quality = 75  # 单文件默认75
            if image_format == 'jpg':
                quality_input = input("🎚 JPG 图片质量（1-95，默认 75）：").strip()
                if quality_input.isdigit():
                    q = int(quality_input)
                    if 1 <= q <= 95:
                        quality = q
                    else:
                        print("⚠️ 质量值超出范围，使用默认75。")
                else:
                    print("⚠️ 质量值无效，使用默认75。")

            if output_path.is_dir():
                out_cbz = output_path / pdf_input.with_suffix('.cbz').name
            else:
                out_cbz = output_path
            _convert_single(pdf_input, out_cbz, image_format, dpi, quality)

        elif pdf_input.is_dir():
            logger.info(f"开始批量转换目录：{pdf_input}")
            pdfs = list(pdf_input.rglob("*.pdf"))
            if not pdfs:
                print("⚠️ 没有找到 PDF 文件。")
                return

            quality = BATCH_JPG_QUALITY_DEFAULT  # 批量默认质量

            success_count = 0
            for i, pdf in enumerate(pdfs, start=1):
                rel = pdf.relative_to(pdf_input).with_suffix('.cbz')
                out_cbz = output_path / rel
                print(f"\n[{i}/{len(pdfs)}] 处理：{pdf}")
                try:
                    _convert_single(pdf, out_cbz, image_format, dpi, quality)
                    success_count += 1
                except Exception as e:
                    logger.exception(f"转换失败：{pdf}\n原因：{e}")
                    print(f"❌ 转换失败：{pdf}\n原因：{e}")
            logger.info(f"完成 {success_count}/{len(pdfs)} 个 PDF 转换")
            print(f"\n✅ 完成 {success_count}/{len(pdfs)} 个 PDF 转换")

        else:
            print("❌ 输入路径无效。")

    except KeyboardInterrupt:
        print("\n⏹ 用户中断，程序退出。")
        sys.exit(0)

def _convert_single(pdf_path, cbz_path, image_format, dpi, jpg_quality):
    print(f"➡️ 开始转换: {pdf_path}")
    logger.info(f"开始转换 PDF：{pdf_path}")

    if dpi is None:
        dpi = analyze_pdf_recommended_dpi(pdf_path)

    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            info = pdfinfo_from_path(str(pdf_path))
            total_pages = info.get("Pages", 0)
            if total_pages == 0:
                raise ValueError("未能获取页数信息。")
        except Exception as e:
            logger.exception(f"无法读取 PDF 信息：{e}")
            print(f"❌ 无法读取 PDF 信息：{e}")
            return

        failures = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            transient=True,
        ) as progress:

            task = progress.add_task("[green]转换中...", total=total_pages)

            for i in range(1, total_pages + 1):
                try:
                    images = convert_from_path(
                        str(pdf_path),
                        dpi=dpi,
                        first_page=i,
                        last_page=i
                    )
                    img = images[0]
                    if image_format == 'jpg':
                        img = img.convert('RGB')
                        img_path = os.path.join(tmp_dir, f"page_{i:03}.jpg")
                        img.save(img_path, quality=jpg_quality)
                    else:
                        img_path = os.path.join(tmp_dir, f"page_{i:03}.{image_format}")
                        img.save(img_path)
                except Exception as e:
                    logger.error(f"第 {i} 页转换失败：{e}")
                    failures.append((i, str(e)))
                progress.update(task, advance=1)

        cbz_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(cbz_path, 'w') as cbz:
            for img_file in sorted(os.listdir(tmp_dir)):
                cbz.write(os.path.join(tmp_dir, img_file), arcname=img_file)

    print(f"\n📦 已保存 CBZ 文件：{cbz_path}")
    logger.info(f"已保存 CBZ 文件：{cbz_path}")
    if failures:
        print(f"⚠️ 有 {len(failures)} 页转换失败：")
        for page, reason in failures:
            print(f" - 第 {page} 页失败：{reason}")
    else:
        print("✅ 所有页面成功转换。")

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
