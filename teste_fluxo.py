"""import re
from playwright.sync_api import sync_playwright, TimeoutError

def testar_todos_os_cursos():
    # Array com os 50 cursos
    cursos = [
        "Pedagogia", "Enfermagem", "Administração", "Análise e Desenvolvimento de Sistemas", 
        "Tecnologia em Gestão de Recursos Humanos", "Terapia Ocupacional", "Farmácia", 
        "Ciências Contábeis", "Educação Física", "Logística", "Gestão Pública", "Fisioterapia", 
        "Biomedicina", "Gestão Comercial", "Marketing", "Gestão Financeira", "Engenharia Civil", 
        "Gestão de Serviços Judiciais e Notariais", "Tecnologia em Processos Gerenciais", 
        "Engenharia Elétrica", "Estética e Cosmética", "Arquitetura e Urbanismo", 
        "Engenharia Mecânica", "Ciências Aeronáuticas", "Gestão da Tecnologia da Informação", 
        "Letras - Português", "Tecnologia em Design de Interiores", "Engenharia de Produção", 
        "História", "Letras - Inglês", "Gestão da Qualidade", "Segurança Pública", 
        "Gestão Ambiental", "Matemática", "Bacharelado em Serviço Social", "Teologia", 
        "Gestão de Trânsito", "Ciências Econômicas", "Ciências Biológicas", "Gestão Hospitalar", 
        "Negócios Imobiliários", "Educação Especial", "Tecnologia em Segurança da Informação", 
        "Tecnologia em Banco de Dados", "Medicina Veterinária", "Ciência da Computação", 
        "Direito", "Fonoaudiologia", "Odontologia", "Psicologia"
    ]
    
    url_afiliado = "https://vest.uninassau.edu.br/cursos?utm_owner=0160101326&utm_profile=Comercial&utm_team=Consultor&modalities=presencial&city=aracaju-se&state=SE"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Inicia o loop por cada curso do array
        for i, curso in enumerate(cursos, 1):
            print(f"\n[{i}/{len(cursos)}] Testando: {curso}")
            
            try:
                # Recarrega a página para limpar o fluxo anterior
                page.goto(url_afiliado)
                page.wait_for_load_state("networkidle")

                # ---------------------------------------------------------
                # MATA-ROLETA
                # ---------------------------------------------------------
                try:
                    botao_close = page.get_by_role("button", name="Close")
                    if botao_close.is_visible(timeout=2000):
                        botao_close.click()
                except Exception:
                    pass

                # ---------------------------------------------------------
                # DESMARCAR O FILTRO PADRÃO (Presencial)
                # ---------------------------------------------------------
                cb_padrao = page.get_by_role("checkbox", name=re.compile("^Presencial", re.IGNORECASE))
                if cb_padrao.is_checked():
                    cb_padrao.uncheck(force=True)
                    page.wait_for_timeout(1000)

                # ---------------------------------------------------------
                # FLUXO DE BUSCA E CLIQUE
                # ---------------------------------------------------------
                campo_curso = page.get_by_role("textbox", name="Nome do curso")
                campo_curso.click(force=True)
                campo_curso.fill(curso)

                page.get_by_role("button", name="Aplicar").click(force=True)
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(1500) 

                # Tenta clicar no Card
                try:
                    page.get_by_role("link", name=re.compile(f"^{curso}", re.IGNORECASE)).first.click(timeout=4000, force=True)
                    print(f"  ✅ Sucesso! Card furado.")
                except TimeoutError:
                    try:
                        page.locator("div").filter(has_text=re.compile(f"^{curso}", re.IGNORECASE)).first.click(force=True, timeout=4000)
                        print(f"  ✅ Sucesso (div alternativa)! Card furado.")
                    except TimeoutError:
                        print(f"  ❌ Falha: O card de {curso} não apareceu nos resultados ou o nome diverge.")
                
                # Pausa rápida para você ver a página de destino antes de recomeçar o loop
                page.wait_for_timeout(1500)

            except Exception as e:
                print(f"  ❌ Erro crítico no fluxo do curso {curso}: {str(e)}")

        context.close()
        browser.close()
        print("\n🔥 Bateria de testes dos 50 cursos finalizada!")

if __name__ == "__main__":
    testar_todos_os_cursos()"""

'''import re
import random
from playwright.sync_api import sync_playwright, TimeoutError

def testar_curso_randomico():
    # Array com os 50 cursos
    cursos = [
        "Pedagogia", "Enfermagem", "Administração", "Análise e Desenvolvimento de Sistemas", 
        "Tecnologia em Gestão de Recursos Humanos", "Terapia Ocupacional", "Farmácia", 
        "Ciências Contábeis", "Educação Física", "Logística", "Gestão Pública", "Fisioterapia", 
        "Biomedicina", "Gestão Comercial", "Marketing", "Gestão Financeira", "Engenharia Civil", 
        "Gestão de Serviços Judiciais e Notariais", "Tecnologia em Processos Gerenciais", 
        "Engenharia Elétrica", "Estética e Cosmética", "Arquitetura e Urbanismo", 
        "Engenharia Mecânica", "Ciências Aeronáuticas", "Gestão da Tecnologia da Informação", 
        "Letras - Português", "Tecnologia em Design de Interiores", "Engenharia de Produção", 
        "História", "Letras - Inglês", "Gestão da Qualidade", "Segurança Pública", 
        "Gestão Ambiental", "Matemática", "Bacharelado em Serviço Social", "Teologia", 
        "Gestão de Trânsito", "Ciências Econômicas", "Ciências Biológicas", "Gestão Hospitalar", 
        "Negócios Imobiliários", "Educação Especial", "Tecnologia em Segurança da Informação", 
        "Tecnologia em Banco de Dados", "Medicina Veterinária", "Ciência da Computação", 
        "Direito", "Fonoaudiologia", "Odontologia", "Psicologia"
    ]
    
    # Sorteia apenas UM curso para o teste
    curso = random.choice(cursos)
    
    url_afiliado = "https://vest.uninassau.edu.br/cursos?utm_owner=0160101326&utm_profile=Comercial&utm_team=Consultor&modalities=presencial&city=aracaju-se&state=SE"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"\n🎲 Curso sorteado para o teste: {curso}")
        
        try:
            # ==========================================
            # PÁGINA 1: BUSCA DO CURSO E CLIQUE NO CARD
            # ==========================================
            page.goto(url_afiliado, wait_until="domcontentloaded")

            # Mata a Roleta Inicial
            try:
                botao_close = page.get_by_role("button", name="Close")
                if botao_close.is_visible(timeout=2000):
                    botao_close.click()
            except Exception:
                pass

            # Desmarcar o filtro 'Presencial' padrão
            cb_padrao = page.get_by_role("checkbox", name=re.compile("^Presencial", re.IGNORECASE))
            if cb_padrao.is_checked():
                cb_padrao.uncheck(force=True)
                page.wait_for_timeout(1000)

            # Busca o curso
            campo_curso = page.get_by_role("textbox", name="Nome do curso")
            campo_curso.click(force=True)
            campo_curso.fill(curso)

            page.get_by_role("button", name="Aplicar").click(force=True)
            page.wait_for_timeout(2000) 

            # Tenta clicar no Card
            try:
                page.get_by_role("link", name=re.compile(f"^{curso}", re.IGNORECASE)).first.click(timeout=8000, force=True)
                print(f"  ✅ Sucesso! Card furado.")
            except TimeoutError:
                try:
                    page.locator("div").filter(has_text=re.compile(f"^{curso}", re.IGNORECASE)).first.click(force=True, timeout=8000)
                    print(f"  ✅ Sucesso (div alternativa)! Card furado.")
                except TimeoutError:
                    print(f"  ❌ Falha: O card de {curso} não apareceu nos resultados.")
                    return
            
            # ==========================================
            # PÁGINA 2: FORMULÁRIO DE INSCRIÇÃO
            # ==========================================
            print(f"  -> Preenchendo formulário para {curso}...")
            
            campo_nome = page.get_by_role("textbox", name="Nome completo")
            campo_nome.wait_for(state="visible", timeout=10000)

            campo_nome.click(force=True)
            campo_nome.fill("Aluno Teste Random")

            campo_email = page.get_by_role("textbox", name="E-mail")
            campo_email.click(force=True)
            campo_email.fill("aluno_random@email.com")

            campo_telefone = page.get_by_role("textbox", name="Telefone/WhatsApp")
            campo_telefone.click(force=True)
            campo_telefone.fill("79999999999")

            btn_noturno = page.get_by_role("button", name="Noturno")
            if btn_noturno.is_visible():
                btn_noturno.click(force=True)

            cb_aceito = page.get_by_role("checkbox", name=re.compile("Li e aceito o", re.IGNORECASE))
            cb_aceito.check(force=True)

            # Clica em inscrever
            btn_inscrever = page.get_by_role("button", name="Quero me inscrever")
            btn_inscrever.click(force=True)

            # O NOVO PASSO ENTRA AQUI: Confirmar e continuar
            print("  -> Aguardando botão de confirmação...")
            btn_confirmar = page.get_by_role("button", name="Confirmar e continuar")
            btn_confirmar.wait_for(state="visible", timeout=10000) # Espera a janela de confirmação aparecer
            btn_confirmar.click(force=True)

            print(f"  ✅ Formulário submetido e confirmado com sucesso! Indo para a página 3...")

            # Pausa de 5 segundos para você conseguir ver a página 3 carregada antes de fechar
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f"  ❌ Erro crítico no fluxo: {str(e)}")

        context.close()
        browser.close()
        print("\n🔥 Teste finalizado!")

if __name__ == "__main__":
    testar_curso_randomico()'''

import re
import random
from playwright.sync_api import sync_playwright, TimeoutError

def testar_curso_randomico():
    # Array com os 50 cursos
    cursos = [
        "Pedagogia", "Enfermagem", "Administração", "Análise e Desenvolvimento de Sistemas", 
        "Tecnologia em Gestão de Recursos Humanos", "Terapia Ocupacional", "Farmácia", 
        "Ciências Contábeis", "Educação Física", "Logística", "Gestão Pública", "Fisioterapia", 
        "Biomedicina", "Gestão Comercial", "Marketing", "Gestão Financeira", "Engenharia Civil", 
        "Gestão de Serviços Judiciais e Notariais", "Tecnologia em Processos Gerenciais", 
        "Engenharia Elétrica", "Estética e Cosmética", "Arquitetura e Urbanismo", 
        "Engenharia Mecânica", "Ciências Aeronáuticas", "Gestão da Tecnologia da Informação", 
        "Letras - Português", "Tecnologia em Design de Interiores", "Engenharia de Produção", 
        "História", "Letras - Inglês", "Gestão da Qualidade", "Segurança Pública", 
        "Gestão Ambiental", "Matemática", "Bacharelado em Serviço Social", "Teologia", 
        "Gestão de Trânsito", "Ciências Econômicas", "Ciências Biológicas", "Gestão Hospitalar", 
        "Negócios Imobiliários", "Educação Especial", "Tecnologia em Segurança da Informação", 
        "Tecnologia em Banco de Dados", "Medicina Veterinária", "Ciência da Computação", 
        "Direito", "Fonoaudiologia", "Odontologia", "Psicologia"
    ]
    
    # Array de turnos para a página 2
    turnos = ["Matutino", "Noturno"]
    
    # Sorteia UM curso e UM turno para o teste
    curso = random.choice(cursos)
    turno_sorteado = random.choice(turnos)
    
    url_afiliado = "https://vest.uninassau.edu.br/cursos?utm_owner=0160101326&utm_profile=Comercial&utm_team=Consultor&modalities=presencial&city=aracaju-se&state=SE"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print(f"\n🎲 Sorteio da rodada -> Curso: {curso} | Turno: {turno_sorteado}")
        
        try:
            # ==========================================
            # PÁGINA 1: BUSCA DO CURSO E CLIQUE NO CARD
            # ==========================================
            page.goto(url_afiliado, wait_until="domcontentloaded")

            # Mata a Roleta Inicial
            try:
                botao_close = page.get_by_role("button", name="Close")
                if botao_close.is_visible(timeout=2000):
                    botao_close.click()
            except Exception:
                pass

            # Desmarcar o filtro 'Presencial' padrão
            cb_padrao = page.get_by_role("checkbox", name=re.compile("^Presencial", re.IGNORECASE))
            if cb_padrao.is_checked():
                cb_padrao.uncheck(force=True)
                page.wait_for_timeout(1000)

            # Busca o curso
            campo_curso = page.get_by_role("textbox", name="Nome do curso")
            campo_curso.click(force=True)
            campo_curso.fill(curso)

            page.get_by_role("button", name="Aplicar").click(force=True)
            page.wait_for_timeout(2000) 

            # Tenta clicar no Card
            try:
                page.get_by_role("link", name=re.compile(f"^{curso}", re.IGNORECASE)).first.click(timeout=8000, force=True)
                print(f"  ✅ Sucesso! Card furado.")
            except TimeoutError:
                try:
                    page.locator("div").filter(has_text=re.compile(f"^{curso}", re.IGNORECASE)).first.click(force=True, timeout=8000)
                    print(f"  ✅ Sucesso (div alternativa)! Card furado.")
                except TimeoutError:
                    print(f"  ❌ Falha: O card de {curso} não apareceu nos resultados.")
                    return
            
            # ==========================================
            # PÁGINA 2: FORMULÁRIO DE INSCRIÇÃO
            # ==========================================
            print(f"  -> Preenchendo formulário...")
            
            campo_nome = page.get_by_role("textbox", name="Nome completo")
            campo_nome.wait_for(state="visible", timeout=10000)

            campo_nome.click(force=True)
            campo_nome.fill("Aluno Teste Random")

            campo_email = page.get_by_role("textbox", name="E-mail")
            campo_email.click(force=True)
            campo_email.fill("aluno_random@email.com")

            campo_telefone = page.get_by_role("textbox", name="Telefone/WhatsApp")
            campo_telefone.click(force=True)
            campo_telefone.fill("79999999999")

            # Clica no turno que foi sorteado
            print(f"  -> Marcando turno: {turno_sorteado}")
            btn_turno = page.get_by_role("button", name=turno_sorteado)
            if btn_turno.is_visible():
                btn_turno.click(force=True)

            cb_aceito = page.get_by_role("checkbox", name=re.compile("Li e aceito o", re.IGNORECASE))
            cb_aceito.check(force=True)

            # Clica em inscrever
            btn_inscrever = page.get_by_role("button", name="Quero me inscrever")
            btn_inscrever.click(force=True)

            # Confirmar e continuar
            print("  -> Aguardando botão de confirmação...")
            btn_confirmar = page.get_by_role("button", name="Confirmar e continuar")
            btn_confirmar.wait_for(state="visible", timeout=10000) 
            btn_confirmar.click(force=True)

            print(f"  ✅ Formulário submetido e confirmado com sucesso! Indo para a página 3...")

            # Pausa de 5 segundos para você conseguir ver a página 3 carregada antes de fechar
            page.wait_for_timeout(5000)

        except Exception as e:
            print(f"  ❌ Erro crítico no fluxo: {str(e)}")

        context.close()
        browser.close()
        print("\n🔥 Teste finalizado!")

if __name__ == "__main__":
    testar_curso_randomico()