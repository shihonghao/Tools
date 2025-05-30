from modules import pdf2cbz

def main():
    while True:
        print("\n=== 🛠 我的工具包 ===")
        print("1. PDF 转 CBZ")
        print("0. 退出")
        choice = input("请选择功能编号：").strip()

        if choice == "1":
            pdf2cbz.convert_pdf_to_cbz_interactive()
        elif choice == "0":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选项，请重新选择。")

if __name__ == "__main__":
    main()
