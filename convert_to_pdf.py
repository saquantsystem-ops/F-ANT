import os
from fpdf import FPDF
from fpdf.enums import XPos, YPos

def md_to_pdf(md_file_path, pdf_file_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    if not os.path.exists(md_file_path):
        print(f"Error: {md_file_path} not found")
        return

    with open(md_file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    for line in lines:
        # Strip potential BOM or weird characters
        line = line.encode('ascii', 'ignore').decode('ascii').strip()
        
        if not line:
            pdf.ln(5)
            continue
        
        if line.startswith("# "):
            pdf.set_font("helvetica", "B", 18)
            pdf.cell(0, 10, line[2:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", size=12)
        elif line.startswith("## "):
            pdf.set_font("helvetica", "B", 14)
            pdf.cell(0, 10, line[3:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", size=12)
        elif line.startswith("---"):
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
            pdf.ln(2)
        elif line.startswith("- "):
            pdf.set_x(20)
            text = line[2:]
            # Handle potential bold parts like **text**:
            if "**" in text:
                parts = text.split("**")
                # parts[0] is before **, parts[1] is bold, parts[2] is after **
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        pdf.set_font("helvetica", "B", 12)
                    else:
                        pdf.set_font("helvetica", size=12)
                    pdf.write(5, part)
            else:
                pdf.set_font("helvetica", size=12)
                pdf.write(5, text)
            pdf.ln(6)
        elif line.startswith("1. ") or line.startswith("2. "):
             pdf.set_x(20)
             pdf.set_font("helvetica", size=12)
             pdf.write(5, line)
             pdf.ln(6)
        else:
            pdf.set_font("helvetica", size=12)
            # Handle bold in paragraph
            if "**" in line:
                parts = line.split("**")
                for i, part in enumerate(parts):
                    if i % 2 == 1:
                        pdf.set_font("helvetica", "B", 12)
                    else:
                        pdf.set_font("helvetica", size=12)
                    pdf.write(6, part)
                pdf.ln(6)
            else:
                pdf.multi_cell(0, 6, line)
            pdf.ln(2)
            
    pdf.output(pdf_file_path)
    print(f"Success: {pdf_file_path} created.")

if __name__ == "__main__":
    md_path = r"c:\Users\DELL\Desktop\jesse_backup\TECH_STACK.md"
    pdf_path = r"c:\Users\DELL\Desktop\jesse_backup\TECH_STACK.pdf"
    md_to_pdf(md_path, pdf_path)
