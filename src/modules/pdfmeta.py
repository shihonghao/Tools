import os
from pypdf import PdfReader, PdfWriter

def set_title_from_filename(input_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    filename = os.path.basename(input_path)
    title = os.path.splitext(filename)[0]

    metadata = reader.metadata
    new_metadata = metadata.copy()
    new_metadata["/Title"] = title
    writer.add_metadata(new_metadata)

    output_path = os.path.splitext(input_path)[0] + "_titled.pdf"

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"✅ {filename} 标题已设置为：{title}")
    print(f"📄 输出文件：{output_path}")

def set_title_from_filename_interactive():
    input_path = input("请输入 PDF 文件路径或文件夹路径：").strip()

    if not os.path.exists(input_path):
        print("❌ 路径不存在，请检查输入。")
        return

    if os.path.isfile(input_path) and input_path.lower().endswith(".pdf"):
        set_title_from_filename(input_path)
    elif os.path.isdir(input_path):
        pdf_files = [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(input_path, f))
        ]

        if not pdf_files:
            print("📂 文件夹中未找到 PDF 文件。")
            return

        print(f"🔍 共找到 {len(pdf_files)} 个 PDF 文件，开始处理…")
        for pdf_file in pdf_files:
            try:
                set_title_from_filename(pdf_file)
            except Exception as e:
                print(f"⚠️ 处理 {pdf_file} 时出错：{e}")
    else:
        print("❌ 无效的路径或文件类型。")

def remove_pdf_title(input_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    metadata = reader.metadata
    new_metadata = metadata.copy()
    new_metadata.pop("/Title", None)  # 移除标题
    writer.add_metadata(new_metadata)

    output_path = os.path.splitext(input_path)[0] + "_no_title.pdf"

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"✅ 已移除标题：{os.path.basename(input_path)}")
    print(f"📄 输出文件：{output_path}")

def remove_pdf_title_interactive():
    input_path = input("请输入 PDF 文件路径或文件夹路径：").strip()

    if not os.path.exists(input_path):
        print("❌ 路径不存在，请检查输入。")
        return

    if os.path.isfile(input_path) and input_path.lower().endswith(".pdf"):
        remove_pdf_title(input_path)
    elif os.path.isdir(input_path):
        pdf_files = [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(input_path, f))
        ]

        if not pdf_files:
            print("📂 文件夹中未找到 PDF 文件。")
            return

        print(f"🔍 共找到 {len(pdf_files)} 个 PDF 文件，开始处理…")
        for pdf_file in pdf_files:
            try:
                remove_pdf_title(pdf_file)
            except Exception as e:
                print(f"⚠️ 处理 {pdf_file} 时出错：{e}")
    else:
        print("❌ 无效的路径或文件类型。")