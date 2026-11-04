"""Roda várias inscrições em paralelo, cada uma num processo próprio.

Por que processo e não thread: a API sync do Playwright não é thread-safe e o
Chromium derruba o processo inteiro em alguns crashes. Com subprocesso, uma
falha não contamina os outros alunos e o paralelismo é real (sem GIL).

IMPORTANTE: o site (vest.uninassau.edu.br) limita POSTs em
/api/enrollment/submit por IP e responde 429 com `retry-after` (~98s, subindo
para ~265s se insistir). Por isso o lote trabalha em ONDAS: no máximo
`--por-onda` alunos por `--janela` segundos. Aumentar isso só gera 429.

Uso:
    python lote_paralelo.py                        # 10 alunos, 4 por onda
    python lote_paralelo.py --alunos 10 --janela 110
    python lote_paralelo.py --visivel              # mostra as janelas (lento)
"""

import argparse
import csv
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SCRIPT = RAIZ / "teste_fluxo.py"
PASTA_LOGS = RAIZ / "logs"
PASTA_RELATORIOS = RAIZ / "relatorios"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def iniciar(indice, headless, carimbo, tentativa):
    """Dispara uma rodada aleatória em subprocesso e devolve o controle dela."""
    sufixo = f"_t{tentativa}" if tentativa > 1 else ""
    run_id = f"p{indice:02d}{sufixo}_{carimbo}"
    log = PASTA_LOGS / f"{run_id}.log"

    ambiente = os.environ.copy()
    ambiente["HEADLESS"] = "1" if headless else "0"

    extra = {}
    if os.name == "nt":
        extra["creationflags"] = subprocess.CREATE_NO_WINDOW

    arquivo = open(log, "w", encoding="utf-8", errors="replace")
    processo = subprocess.Popen(
        [sys.executable, str(SCRIPT), "1"],
        cwd=str(RAIZ),
        env=ambiente,
        stdout=arquivo,
        stderr=subprocess.STDOUT,
        **extra,
    )

    return {
        "indice": indice,
        "tentativa": tentativa,
        "run_id": run_id,
        "processo": processo,
        "log": log,
        "arquivo": arquivo,
        "inicio": time.time(),
        "curso": "?",
        "turno": "?",
        "aluno": "?",
        "email": "?",
        "duracao": 0.0,
        "ok": False,
        "limite_taxa": 0,
    }


def finalizar(item):
    """Fecha o subprocesso, lê o log e extrai os dados da rodada."""
    item["arquivo"].close()
    item["processo"].wait()
    item["duracao"] = round(time.time() - item["inicio"], 1)
    item["ok"] = item["processo"].returncode == 0

    try:
        texto = item["log"].read_text(encoding="utf-8", errors="replace")
    except Exception:
        texto = ""

    casamento = re.search(r"Curso:\s*(.+?)\s*\|\s*Turno:\s*(.+)", texto)
    if casamento:
        item["curso"] = casamento.group(1).strip()
        item["turno"] = casamento.group(2).strip()

    casamento = re.search(r"Nome:\s*(.+?)\s*\|\s*E-mail:\s*(\S+)", texto)
    if casamento:
        item["aluno"] = casamento.group(1).strip()
        item["email"] = casamento.group(2).strip()

    casamento = re.search(r"tentar novamente em (\d+)s", texto)
    if casamento:
        item["limite_taxa"] = int(casamento.group(1))

    return item


def rodar_onda(fila, workers, headless, carimbo, tentativas):
    """Executa a fila da onda respeitando o paralelismo e devolve os resultados."""
    ativos = []
    concluidos = []
    fila = list(fila)

    while fila or ativos:
        while fila and len(ativos) < workers:
            indice = fila.pop(0)
            tentativa = tentativas.get(indice, 1)
            item = iniciar(indice, headless, carimbo, tentativa)
            ativos.append(item)
            print(f"  ▶ aluno {indice} iniciado ({item['run_id']})", flush=True)

        time.sleep(0.4)

        for item in list(ativos):
            if item["processo"].poll() is None:
                continue

            ativos.remove(item)
            finalizar(item)
            concluidos.append(item)

            if item["ok"]:
                print(
                    f"  ✅ aluno {item['indice']} | {item['curso']} "
                    f"({item['turno']}) | {item['duracao']}s | {item['aluno']}",
                    flush=True,
                )
            else:
                extra = (
                    f" | 429, retry em {item['limite_taxa']}s"
                    if item["limite_taxa"]
                    else ""
                )
                print(
                    f"  ❌ aluno {item['indice']} | {item['curso']} "
                    f"({item['turno']}) | {item['duracao']}s{extra}",
                    flush=True,
                )

    return concluidos


def salvar_relatorio(resultados, carimbo):
    PASTA_RELATORIOS.mkdir(exist_ok=True)
    destino = PASTA_RELATORIOS / f"lote_{carimbo}.csv"

    with open(destino, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(
            [
                "indice",
                "tentativa",
                "run_id",
                "aluno",
                "email",
                "curso",
                "turno",
                "ok",
                "duracao_s",
                "log",
            ]
        )
        for item in sorted(resultados, key=lambda x: (x["indice"], x["tentativa"])):
            escritor.writerow(
                [
                    item["indice"],
                    item["tentativa"],
                    item["run_id"],
                    item["aluno"],
                    item["email"],
                    item["curso"],
                    item["turno"],
                    "OK" if item["ok"] else "FALHOU",
                    item["duracao"],
                    item["log"].name,
                ]
            )

    return destino


def main():
    parser = argparse.ArgumentParser(description="Lote paralelo de inscrições")
    parser.add_argument("--alunos", type=int, default=10, help="quantidade de alunos")
    parser.add_argument("--workers", type=int, default=4, help="execuções simultâneas")
    parser.add_argument(
        "--por-onda",
        type=int,
        default=4,
        help="inscrições por janela (o site bloqueia acima disso)",
    )
    parser.add_argument(
        "--janela",
        type=float,
        default=105,
        help="segundos entre ondas (o retry-after do site fica em ~98s)",
    )
    parser.add_argument(
        "--max-tentativas",
        type=int,
        default=3,
        help="tentativas por aluno quando o site responde 429",
    )
    parser.add_argument(
        "--visivel",
        action="store_true",
        help="abre as janelas do navegador (padrão: headless)",
    )
    args = parser.parse_args()

    total = max(1, args.alunos)
    workers = max(1, min(args.workers, args.por_onda))
    por_onda = max(1, args.por_onda)
    headless = not args.visivel

    PASTA_LOGS.mkdir(exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    geral_inicio = time.time()

    print("=" * 70)
    print(
        f"LOTE PARALELO | {total} alunos | {workers} simultâneos | "
        f"{por_onda} por janela de {args.janela:.0f}s | "
        f"{'headless' if headless else 'janelas visíveis'}"
    )
    print(f"início: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70, flush=True)

    pendentes = list(range(1, total + 1))
    tentativas = {i: 1 for i in pendentes}
    resultados = []
    onda = 0

    while pendentes:
        onda += 1
        inicio_onda = time.time()
        lote = pendentes[:por_onda]
        pendentes = pendentes[por_onda:]

        print(f"\n--- onda {onda} | alunos {lote} ---", flush=True)
        concluidos = rodar_onda(lote, workers, headless, carimbo, tentativas)
        resultados.extend(concluidos)

        # Reagenda quem bateu no limite do site.
        for item in concluidos:
            if item["ok"] or not item["limite_taxa"]:
                continue
            if tentativas.get(item["indice"], 1) >= args.max_tentativas:
                print(
                    f"  ⚠️ aluno {item['indice']} desistiu após "
                    f"{tentativas[item['indice']]} tentativas",
                    flush=True,
                )
                continue
            tentativas[item["indice"]] += 1
            pendentes.insert(0, item["indice"])
            print(
                f"  🔁 aluno {item['indice']} reagendado "
                f"(tentativa {tentativas[item['indice']]})",
                flush=True,
            )

        if pendentes:
            espera = args.janela - (time.time() - inicio_onda)
            if espera > 0:
                print(
                    f"  ⏳ aguardando {espera:.0f}s para respeitar o limite do site",
                    flush=True,
                )
                time.sleep(espera)

    decorrido = time.time() - geral_inicio
    aprovados = sum(1 for r in resultados if r["ok"])

    print("\n" + "=" * 70)
    print("RESUMO (uma linha por tentativa)")
    print("=" * 70)
    for item in sorted(resultados, key=lambda x: (x["indice"], x["tentativa"])):
        marca = "✅" if item["ok"] else "❌"
        print(
            f"  {marca} {item['indice']:2} t{item['tentativa']} | "
            f"{item['curso'][:26]:26} | {item['turno'][:9]:9} | "
            f"{item['duracao']:6.1f}s | {item['aluno']}"
        )

    minutos = decorrido / 60
    por_minuto = aprovados / minutos if minutos > 0 else 0

    print(f"\n  Sucesso: {aprovados}/{total} alunos")
    print(f"  Tempo total: {decorrido:.1f}s ({minutos:.2f} min)")
    print(f"  Vazão efetiva: {por_minuto:.2f} alunos/min")
    print(f"  Relatório: {salvar_relatorio(resultados, carimbo)}")
    print(f"  Logs: {PASTA_LOGS}")
    print(
        "\n  Obs: o teto não é o navegador — é o rate limit do site "
        f"(~{por_onda} inscrições a cada {args.janela:.0f}s)."
    )

    sys.exit(0 if aprovados == total else 1)


if __name__ == "__main__":
    main()
