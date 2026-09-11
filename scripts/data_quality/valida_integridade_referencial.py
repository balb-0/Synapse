#!/usr/bin/env python3
"""Verifica o alinhamento entre o modelo de dados (DER) e as bases reais.

Confronta cada relacionamento (chave estrangeira) previsto no modelo relacional
da Central de Pesquisas com os dados disponibilizados pelo parceiro, medindo a
integridade referencial e listando as chaves órfãs. Serve de evidência para o
card de teste "Verificar alinhamento entre o diagrama Entidade-Relacionamento e
os passos do fluxo" — o alinhamento fluxo↔banco só está mapeado se cada relação
do DER se sustentar (ou tiver sua exceção documentada) nos dados.

Relacionamentos verificados:
    questoes.pesquisa_id       -> pesquisas.id
    respostas.pesquisa_id      -> pesquisas.id
    respostas.id_pergunta      -> questoes.id_pergunta
    respostas.id_empresa       -> empresas.ID
    respondentes.id_pesq       -> pesquisas.id
    respondentes.id_empresa    -> empresas.ID
    respondentes.id_cliente    -> clientes.id_cliente
    clientes.id_empresa        -> empresas.ID

As bases contêm dados pessoais e NÃO são versionadas (LGPD); aponte o script para
o diretório seguro local. Apenas agregados e chaves técnicas são impressos.

Uso:
    python scripts/data_quality/valida_integridade_referencial.py [DIR_BASES]

Código de saída: 0 se toda relação tem cobertura de 100% OU órfãos já
documentados como exceção; 1 se surgir órfão não previsto.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Órfãos já conhecidos e documentados (chaves de pesquisa a reconciliar com o
# parceiro — ver §2.8 do documento de Governança e §6.7.10 do projeto.md).
ORFAOS_DOCUMENTADOS = {"424", "1116", "1139", "1147", "304"}

# (base_filha, coluna_fk) -> (base_pai, coluna_pk)
RELACOES = [
    ("questoes", "pesquisa_id", "pesquisas", "id"),
    ("respostas", "pesquisa_id", "pesquisas", "id"),
    ("respostas", "id_pergunta", "questoes", "id_pergunta"),
    ("respostas", "id_empresa", "empresas", "ID"),
    ("respondentes", "id_pesq", "pesquisas", "id"),
    ("respondentes", "id_empresa", "empresas", "ID"),
    ("respondentes", "id_cliente", "clientes", "id_cliente"),
    ("clientes", "id_empresa", "empresas", "ID"),
]


def carregar(caminho: Path) -> tuple[list[str], list[list[str]]]:
    for enc in ("utf-8-sig", "latin1"):
        try:
            with open(caminho, encoding=enc, newline="") as f:
                amostra = f.read(4096)
                f.seek(0)
                delim = ";" if amostra.count(";") > amostra.count(",") else ","
                linhas = list(csv.reader(f, delimiter=delim))
            cabecalho = [c.strip().lstrip("﻿") for c in linhas[0]]
            dados = [r for r in linhas[1:] if any(c.strip() for c in r)]
            return cabecalho, dados
        except UnicodeDecodeError:
            continue
    raise SystemExit(f"[erro] não foi possível ler {caminho}")


def coluna(cabecalho: list[str], dados: list[list[str]], nome: str) -> list[str]:
    i = cabecalho.index(nome)
    return [r[i].strip() for r in dados if i < len(r) and r[i].strip()]


def main(dir_bases: str = "insumos") -> int:
    raiz = Path(dir_bases)
    if not raiz.is_dir():
        raise SystemExit(f"[erro] diretório de bases não encontrado: {raiz}")

    # carrega os conjuntos de chaves primárias uma única vez
    cache: dict[str, tuple[list[str], list[list[str]]]] = {}
    for nome in {r[0] for r in RELACOES} | {r[2] for r in RELACOES}:
        cache[nome] = carregar(raiz / f"{nome}.csv")

    print("=" * 92)
    print("ALINHAMENTO DER x DADOS REAIS — integridade referencial por relacionamento")
    print("=" * 92)
    print(f"{'relacionamento':52s} {'distintas':>9s} {'órfãs':>6s} {'cobertura':>9s}  status")

    houve_orfao_novo = False
    for base_f, fk, base_p, pk in RELACOES:
        hf, df = cache[base_f]
        hp, dp = cache[base_p]
        universo = set(coluna(hp, dp, pk))
        valores = set(coluna(hf, df, fk))
        orfas = sorted(valores - universo, key=lambda x: (len(x), x))
        total = len(valores)
        cob = 100.0 * (total - len(orfas)) / total if total else 100.0
        novas = [o for o in orfas if o not in ORFAOS_DOCUMENTADOS]
        if novas:
            houve_orfao_novo = True
            status = f"NOVO ÓRFÃO {novas[:5]}"
        elif orfas:
            status = f"órfãos documentados {orfas[:5]}"
        else:
            status = "OK (íntegro)"
        rel = f"{base_f}.{fk} -> {base_p}.{pk}"
        print(f"{rel:52s} {total:9d} {len(orfas):6d} {cob:8.1f}%  {status}")

    print()
    print(
        "Órfãos documentados (exceção conhecida, reter e reconciliar):",
        ", ".join(sorted(ORFAOS_DOCUMENTADOS, key=lambda x: (len(x), x))),
    )
    print(
        "Resultado:",
        "ALINHAMENTO OK" if not houve_orfao_novo else "ATENÇÃO — órfão não previsto encontrado",
    )
    return 0 if not houve_orfao_novo else 1


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else "insumos"
    raise SystemExit(main(destino))
