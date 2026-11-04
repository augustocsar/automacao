# Experimento: lote paralelo (abandonado)

Tentativa de rodar várias inscrições ao mesmo tempo para aumentar a vazão.

## Por que foi abandonado

O gargalo **não é o código**: o site limita `POST /api/enrollment/submit` por IP
e devolve **HTTP 429** com `retry-after: 98` (e `265` se insistir). É um rate
limit no CloudFront.

Resultado do teste com 10 alunos / 4 simultâneos: **4 OK e 6 falhas**, todas com
429 depois das primeiras 4 inscrições. Teto real do site: **~4 inscrições a
cada 100 segundos** (~2,4/min). Ou seja, 10/min é impossível por limitação do
servidor, não da automação.

## O que tem aqui

| Arquivo | O que é |
|---|---|
| `teste_fluxo_paralelo.py` | Cópia do `teste_fluxo.py` com `executar_fluxo()` parametrizado, `HEADLESS` por env, detecção de 429 (`LimiteDeTaxa`) e retry no `main()` |
| `lote_paralelo.py` | Orquestrador por subprocessos, com ondas de 4 alunos a cada 110s |
| `logs/` | Log de cada rodada do lote |
| `relatorios/` | CSV consolidado do lote |

## Como rodar (se precisar retomar)

```powershell
# 10 alunos, 4 por onda de 110s (~4 min)
.\venv\Scripts\python.exe _experimentos\lote_paralelo.py --alunos 10 --workers 4
```

O `lote_paralelo.py` depende do `teste_fluxo_paralelo.py` ao lado dele — por
isso os dois estão juntos nesta pasta. O `teste_fluxo.py` da raiz **não** tem
mais o `executar_fluxo()`.
