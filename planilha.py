'''import pandas as pd
import re

def testar_leitura_planilha():
    nome_arquivo = "Base_Alunos_17_Cursos_Finais.xlsx"
    print(f"Lendo os dados de: {nome_arquivo}...\n")
    
    try:
        df = pd.read_excel(nome_arquivo)
        
        for index, row in df.iterrows():
            nome = str(row.get('Nome', 'NÃO ENCONTRADO')).strip()
            curso = str(row.get('Curso', 'NÃO ENCONTRADO')).strip()
            turno = str(row.get('Turno', 'NÃO ENCONTRADO')).strip()
            email = str(row.get('Email', 'NÃO ENCONTRADO')).strip()
            telefone = str(row.get('Telefone', 'NÃO ENCONTRADO')).replace('.0', '').strip()
            modalidade = str(row.get('Modalidade', 'NÃO ENCONTRADO')).strip()
            
            cpf = str(row.get('CPF', 'NÃO ENCONTRADO')).replace('.0', '').strip()
            
            data_nasc_crua = row.get('Data_Nascimento', 'NÃO ENCONTRADO')
            if pd.notna(data_nasc_crua) and hasattr(data_nasc_crua, 'strftime'):
                data_nasc = data_nasc_crua.strftime('%d/%m/%Y')
            else:
                data_nasc = str(data_nasc_crua).replace(' 00:00:00', '').strip()

            # =======================================================
            # SEPARAÇÃO DE CEP, NÚMERO E BAIRRO
            # =======================================================
            endereco_cru = str(row.get('Endereco_Completo', '')).strip()
            cep_final = "NÃO ENCONTRADO"
            endereco_final = "NÃO ENCONTRADO"
            numero_final = "S/N"
            bairro_final = "Centro" # Valor padrão caso não ache nada
            
            if endereco_cru and endereco_cru.lower() != 'nan':
                resto = endereco_cru
                
                # 1. Extrai o CEP
                match_cep = re.search(r'\b\d{5}-?\d{3}\b', resto)
                if match_cep:
                    cep_final = match_cep.group(0)
                    resto = resto.replace(cep_final, '')
                
                # Limpa rótulos iniciais
                resto = re.sub(r'(?i)cep:?|end:?|\|', '', resto).strip()
                
                # 2. Extrai o Número
                match_num = re.search(r'(?i)(?:,\s*)?(?:n[º°.:]?\s*|número\s*|numero\s*)+(\d+[a-zA-Z]?)', resto)
                if match_num:
                    numero_final = match_num.group(1)
                    resto = resto.replace(match_num.group(0), '')
                else:
                    match_num_virgula = re.search(r',\s*(\d+[a-zA-Z]?)\b', resto)
                    if match_num_virgula:
                        numero_final = match_num_virgula.group(1)
                        resto = resto.replace(match_num_virgula.group(0), '')

                # 3. Extrai o Bairro
                match_bairro = re.search(r'(?i)\b(?:bairro|loteamento|lot\.|conjunto|conj\.|residencial|res\.|povoado|pov\.)\s*[:\-]?\s*([^,;]+)', resto)
                if match_bairro:
                    bairro_final = match_bairro.group(1).strip()
                    resto = resto.replace(match_bairro.group(0), '')
                else:
                    # Se não tem a palavra explícita, remove "Aracaju", "Sergipe" e "SE"
                    resto_limpo = re.sub(r'(?i)\b(?:aracaju|sergipe|se|brasil)\b', '', resto).strip(' ,.-')
                    
                    # Pega o que sobrou após a última vírgula como sendo o bairro
                    partes = [p.strip() for p in resto_limpo.split(',') if p.strip()]
                    if len(partes) > 1:
                        bairro_final = partes[-1]
                        resto = resto.replace(bairro_final, '')
                
                # 4. Limpeza final da Rua
                resto = re.sub(r'^[,.\-\s]+', '', resto)
                resto = re.sub(r'[,.\-\s]+$', '', resto)
                
                if resto:
                    endereco_final = resto

            print(f"Aluno {index + 1}:")
            print(f" 👤 Nome:       {nome}")
            print(f" 🎓 Curso:      {curso}")
            print(f" 🏫 Modalidade: {modalidade}")
            print(f" ☀️ Turno:      {turno}")
            print(f" 📧 Email:      {email}")
            print(f" 📱 Tel:        {telefone}")
            print(f" 🪪 CPF:        {cpf}")
            print(f" 📅 Data Nasc.: {data_nasc}")
            print(f" 📮 CEP Isolado:{cep_final}")
            print(f" 📍 Rua Limpa:  {endereco_final}")
            print(f" 🏘️ Bairro:     {bairro_final}")
            print(f" 🔢 Número Ext.:{numero_final}")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Erro ao ler a planilha: {e}")

if __name__ == "__main__":
    testar_leitura_planilha()'''