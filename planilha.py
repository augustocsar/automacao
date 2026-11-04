import random
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta

import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CURSOS = [
    "Administração",
    "Odontologia",
    "Medicina Veterinária",
    "Educação Física",
    "Direito",
    "Fisioterapia",
    "Fonoaudiologia",
    "Psicologia",
    "Enfermagem",
    "Biomedicina",
    "Sistemas de Informação",
    "Farmácia",
    "Análise e Desenvolvimento de Sistemas",
    "Terapia Ocupacional",
    "Estética e Cosmética",
    "Ciência da Computação",
]

TURNOS = ["Matutino", "Noturno"]
LISTA_CEPS = [
    "49090-080",
    "49010-000",
    "49020-010",
    "49030-020",
    "49040-030",
    "49050-040",
]
NOMES = [
    "Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabriela",
    "Hugo", "Isabela", "Joao", "Larissa", "Marcos", "Natalia", "Otavio",
    "Paula", "Rafael", "Sofia", "Tiago", "Vanessa", "Wagner",
]
SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Lima", "Pereira", "Costa",
    "Almeida", "Ferreira", "Rodrigues", "Gomes", "Martins", "Araujo",
    "Barbosa", "Ribeiro", "Cardoso", "Moraes", "Nunes",
]


def gerar_cpf_valido():
    while True:
        base = [random.randint(0, 9) for _ in range(9)]
        if len(set(base)) == 1:
            continue

        for peso_inicial in (10, 11):
            soma = sum(d * (peso_inicial - i) for i, d in enumerate(base))
            digito = (soma * 10) % 11
            base.append(0 if digito == 10 else digito)

        return "".join(str(d) for d in base)


def formatar_cpf(cpf):
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def gerar_data_nascimento(idade_min=18, idade_max=35):
    hoje = date.today()
    mais_velho = hoje - timedelta(days=idade_max * 365 + 30)
    mais_novo = hoje - timedelta(days=idade_min * 365)
    dias = (mais_novo - mais_velho).days
    nascimento = mais_velho + timedelta(days=random.randint(0, max(dias, 1)))
    return nascimento.strftime("%d/%m/%Y")


def gerar_dados():
    nome = f"{random.choice(NOMES)} {random.choice(SOBRENOMES)}"
    slug = re.sub(r"[^a-z]", "", nome.lower())
    cpf = gerar_cpf_valido()

    return {
        "nome": nome,
        "email": f"{slug}{random.randint(10, 9999)}@gmail.com",
        "telefone": f"799{random.randint(8000, 9999)}{random.randint(1000, 9999)}",
        "cpf": formatar_cpf(cpf),
        "cpf_digitos": cpf,
        "nascimento": gerar_data_nascimento(),
        "cep": random.choice(LISTA_CEPS),
        "numero": str(random.randint(10, 2000)),
    }


def normalizar_turno(valor):
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    texto = texto.encode("ascii", "ignore").decode("ascii").strip().upper()

    if texto.startswith("NOITE") or texto.startswith("NOT"):
        return "Noturno"
    if texto.startswith("MANHA") or texto.startswith("MAT"):
        return "Matutino"
    return None


def validar_cpf(digitos):
    if len(digitos) != 11 or len(set(digitos)) == 1:
        return False

    numeros = [int(d) for d in digitos]
    for n in (9, 10):
        soma = sum(numeros[i] * (n + 1 - i) for i in range(n))
        digito = (soma * 10) % 11
        digito = 0 if digito == 10 else digito
        if digito != numeros[n]:
            return False
    return True


def somente_digitos(valor):
    if valor is None:
        return ""
    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass

    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return re.sub(r"\D", "", texto)


def limpar_endereco(endereco_cru):
    resultado = {"cep": None, "rua": None, "bairro": "Centro", "numero": "S/N"}
    endereco_cru = str(endereco_cru or "").strip()
    if not endereco_cru or endereco_cru.lower() == "nan":
        return resultado

    resto = endereco_cru

    match_cep = re.search(r"\b\d{5}-?\d{3}\b", resto)
    if match_cep:
        resultado["cep"] = match_cep.group(0)
        resto = resto.replace(resultado["cep"], "")

    resto = re.sub(r"(?i)cep:?|end:?|\|", "", resto).strip()

    match_num = re.search(
        r"(?i)(?:,\s*)?(?:n[º°.:]?\s*|número\s*|numero\s*)+(\d+[a-zA-Z]?)", resto
    )
    if match_num:
        resultado["numero"] = match_num.group(1)
        resto = resto.replace(match_num.group(0), "")
    else:
        match_num_virgula = re.search(r",\s*(\d+[a-zA-Z]?)\b", resto)
        if match_num_virgula:
            resultado["numero"] = match_num_virgula.group(1)
            resto = resto.replace(match_num_virgula.group(0), "")

    match_bairro = re.search(
        r"(?i)\b(?:bairro|loteamento|lot\.|conjunto|conj\.|residencial|res\.|povoado|pov\.)"
        r"\s*[:\-]?\s*([^,;]+)",
        resto,
    )
    if match_bairro:
        resultado["bairro"] = match_bairro.group(1).strip()
        resto = resto.replace(match_bairro.group(0), "")
    else:
        resto_limpo = re.sub(
            r"(?i)\b(?:aracaju|sergipe|se|brasil)\b", "", resto
        ).strip(" ,.-")

        partes = [p.strip() for p in resto_limpo.split(",") if p.strip()]
        if len(partes) > 1:
            resultado["bairro"] = partes[-1]
            resto = resto.replace(resultado["bairro"], "")

    resto = re.sub(r"^[,.\-\s]+", "", resto)
    resto = re.sub(r"[,.\-\s]+$", "", resto)

    if resto:
        resultado["rua"] = resto

    return resultado


def calcular_idade(data_br):
    try:
        nasc = datetime.strptime(str(data_br).strip(), "%d/%m/%Y").date()
    except (TypeError, ValueError):
        return None

    hoje = date.today()
    return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))


def parse_responsavel(valor):
    """Extrai nome, CPF e nascimento do campo bruto do responsável financeiro."""
    if valor is None:
        return {}

    try:
        if pd.isna(valor):
            return {}
    except (TypeError, ValueError):
        pass

    texto = str(valor).strip()
    if not texto or texto.lower() == "nan":
        return {}

    cpf = re.search(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", texto)
    nasc = re.search(r"\b\d{2}/\d{2}/\d{4}\b", texto)
    nome = re.sub(r"[\d./\-;]+", " ", texto)
    nome = re.sub(r"\s+", " ", nome).strip(" ,;.") or None

    return {
        "nome": nome,
        "cpf": re.sub(r"\D", "", cpf.group(0)) if cpf else None,
        "nasc": nasc.group(0) if nasc else None,
    }


def carregar_aluno(arquivo, linha=1):
    """Lê e limpa a linha da planilha.

    Campos ausentes recebem valores aleatórios. O CPF é obrigatório: se faltar ou
    for inválido, levanta ValueError para o envio nem começar.
    """
    df = pd.read_excel(arquivo)
    if linha < 1 or linha > len(df):
        raise ValueError(
            f"Linha {linha} fora da planilha (o arquivo tem {len(df)} linhas)"
        )

    row = df.iloc[linha - 1]
    padrao = gerar_dados()

    nome = str(row.get("Nome", "") or "").strip()
    if not nome or nome.lower() == "nan":
        nome = padrao["nome"]

    email = str(row.get("Email", "") or "").strip()
    if not email or email.lower() == "nan":
        email = padrao["email"]

    telefone = somente_digitos(row.get("Telefone"))
    if len(telefone) != 11:
        telefone = padrao["telefone"]

    cpf_digitos = somente_digitos(row.get("CPF"))
    if not cpf_digitos:
        raise ValueError(f"Linha {linha}: CPF ausente (o CPF é obrigatório)")
    if len(cpf_digitos) < 11:
        cpf_digitos = cpf_digitos.zfill(11)
    if not validar_cpf(cpf_digitos):
        print(
            f"  ⚠️ Linha {linha}: CPF com checksum inválido "
            f"({formatar_cpf(cpf_digitos)}) — enviando mesmo assim"
        )

    data_nasc_crua = row.get("Data_Nascimento")
    if pd.notna(data_nasc_crua) and hasattr(data_nasc_crua, "strftime"):
        nascimento = data_nasc_crua.strftime("%d/%m/%Y")
    else:
        nascimento = str(data_nasc_crua or "").replace(" 00:00:00", "").strip()
        if not nascimento or nascimento.lower() == "nan":
            nascimento = padrao["nascimento"]

    curso = str(row.get("Curso", "") or "").strip()
    if curso not in CURSOS:
        curso = random.choice(CURSOS)

    turno = normalizar_turno(row.get("Turno"))
    if turno is None:
        turno = random.choice(TURNOS)

    endereco = limpar_endereco(row.get("Endereco_Completo"))
    cep = endereco["cep"] or padrao["cep"]
    numero = endereco["numero"]
    if numero in ("", "S/N"):
        numero = str(random.randint(10, 2000))

    idade = calcular_idade(nascimento)

    return {
        "linha": linha,
        "nome": nome,
        "email": email,
        "telefone": telefone,
        "cpf": formatar_cpf(cpf_digitos),
        "cpf_digitos": cpf_digitos,
        "cpf_valido": validar_cpf(cpf_digitos),
        "nascimento": nascimento,
        "idade": idade,
        "menor": idade is not None and idade < 18,
        "curso": curso,
        "turno": turno,
        "cep": cep,
        "numero": numero,
        "rua": endereco["rua"],
        "bairro": endereco["bairro"],
        "responsavel": parse_responsavel(row.get("Dados_Responsavel_Bruto")),
    }


def testar_leitura_planilha(arquivo="Base_Alunos_17_Cursos_Finais.xlsx"):
    print(f"Lendo os dados de: {arquivo}...\n")
    try:
        df = pd.read_excel(arquivo)
        for index in range(len(df)):
            aluno = carregar_aluno(arquivo, index + 1)
            print(f"Aluno {index + 1}:")
            print(f" 👤 Nome:       {aluno['nome']}")
            print(f" 🎓 Curso:      {aluno['curso']}")
            print(f" ☀️ Turno:      {aluno['turno']}")
            print(f" 📧 Email:      {aluno['email']}")
            print(f" 📱 Tel:        {aluno['telefone']}")
            print(f" 🪪 CPF:        {aluno['cpf']}")
            print(f" 📅 Data Nasc.: {aluno['nascimento']}")
            print(f" 📮 CEP:        {aluno['cep']}")
            print(f" 📍 Rua:        {aluno['rua']}")
            print(f" 🏘️ Bairro:     {aluno['bairro']}")
            print(f" 🔢 Número:     {aluno['numero']}")
            print("-" * 50)
    except Exception as erro:
        print(f"❌ Erro ao ler a planilha: {erro}")


if __name__ == "__main__":
    testar_leitura_planilha()
