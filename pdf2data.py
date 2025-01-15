import pdfplumber

def extract_data_from_pdf(pdf_path):

    result = {'zakázka': [], 'položky': []}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            # Najít řádek se zakázkou
            if 'Zakázka:' in text:
                zakazka_line = [line for line in text.split('\n') if 'Zakázka:' in line][0]
                zakazka_parts = zakazka_line.replace('Zakázka:', '').replace("účtu: 43-8706260257/0100 ", "").strip().split(' ', 1)
                zakazka_number = zakazka_parts[1].strip().split(' ')[0]
                zakazka_name = " ".join(zakazka_parts[1].strip().split(' ')[1:])
                result['zakázka'] = [[zakazka_number], [zakazka_name]]

            # Najít položky
            for line in text.split('\n'):
                if 'ks' in line:
                    parts = line.split(' ')
                    code = parts[0].strip()
                    name = " ".join(parts[1:(len(parts)-3)])
                    qt = int(float(parts[(len(parts)-3)].replace(",", ".")))
                    result['položky'].append([[code], [name], [qt]])

    return result


# pdf_path = "C.pdf"  # Nahraďte cestou k vašemu PDF souboru
# result_dict = extract_data_from_pdf(pdf_path)
# print(result_dict)
