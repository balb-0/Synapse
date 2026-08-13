#!/usr/bin/env python3
"""
gerar-dados-prototipos.py

Gera o arquivo JSON determinístico (dados-dashboard.json) a partir das fontes CSV
do Sindusfarma/Central de Pesquisas.

Regras:
- Python stdlib apenas.
- CLI: --input-dir, --output, --processado-em
- Suporte a SOURCE_DATE_EPOCH
- Escrita atômica (.tmp -> rename)
- UTF-8 BOM em CSVs (; delimitador, vírgula decimal)
- Agregados sem exposição de dados pessoais ou identificadores individuais
"""

import os
import sys
import csv
import json
import hashlib
import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP


ESQUEMAS = {
    'clientes': ['id_cliente', 'id_empresa', 'cargo', 'departamento', 'e-mail'],
    'empresas': ['ID', 'Nome Fantasia', '% de mercado', 'Nacionalidade', 'Associado', 'Tipo de Associado', 'Cidade', 'Estado', 'País'],
    'pesquisas': [
        'id', 'titulo', 'status', 'tipo', 'area', 'participantes', 'part_mercado',
        'data_solicitacao', 'data_aprov', 'data_divulgacao', 'data_limite',
        'prorrogada_ate', 'data_entrega', 'dias_uteis_para_entrega',
        'complexidade', 'tipo de resposta', 'tempo_preenchimento', 'objetivos',
        'dia da semana de lançamento', 'dias úteis aberta',
        'dias entre a solicitação e a divulgação', 'dias para tabulação',
    ] + [''] * 11,
    'questoes': [
        'id_pergunta', 'pesquisa_id', 'pesquisa_titulo', 'enunciado', 'tipo',
        'qtd_alternativas', 'alternativas', 'linhas_matriz', 'colunas_matriz',
        'confianca', 'formato_arquivo', 'col_origem', 'observacoes',
    ],
    'respondentes': ['id_pesq', 'hora_inicio', 'hora_termino', 'id_empresa', 'market_share', 'id_cliente'],
    'respostas': [
        'id_resposta', 'pesquisa_id', 'id_pergunta', 'respondent_id',
        'id_empresa', 'alternativa', 'linha_matriz', 'coluna_matriz', 'valor',
    ],
}

CHAVES_CANDIDATAS = {
    'clientes': ('id_cliente',),
    'empresas': ('ID',),
    'pesquisas': ('id',),
    'questoes': ('id_pergunta',),
    'respondentes': None,
    'respostas': ('id_resposta',),
}


def round_pct(num, den):
    if den is None or den == 0:
        return None
    val = (Decimal(str(num)) / Decimal(str(den))) * Decimal('100')
    return float(val.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP))


def format_pct(val):
    if val is None:
        return None
    s = f"{val:.1f}".replace('.', ',')
    return f"{s}%"


def load_csv(filepath, source_id):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Arquivo CSV obrigatório não encontrado: {filepath}")
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        if reader.fieldnames != ESQUEMAS[source_id]:
            raise ValueError(
                f"Esquema incompatível em {os.path.basename(filepath)}: "
                f"esperado {ESQUEMAS[source_id]!r}; recebido {reader.fieldnames!r}"
            )
        rows = list(reader)
    return rows


def compute_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def valor_semantico(value):
    value = value.strip()
    return value if value and value.lower() not in {'s/i', 'na', 'n/a'} else None


def decimal_localizado(value):
    value = value.removesuffix('%').strip()
    if ',' in value:
        value = value.replace('.', '').replace(',', '.')
    return Decimal(value)


def perfil_parseabilidade(rows, field, kind, formats=None):
    values = [value for row in rows if (value := valor_semantico(row.get(field, ''))) is not None]

    def valid(value):
        try:
            if kind == 'data':
                return any(_try_datetime(value, fmt) for fmt in formats)
            parsed = decimal_localizado(value)
            return kind != 'inteiro' or parsed == parsed.to_integral_value()
        except (ValueError, ArithmeticError):
            return False

    validos = sum(1 for value in values if valid(value))
    return {
        'campo': field,
        'tipo': kind,
        'validos': validos,
        'avaliados': len(values),
    }


def perfil_duplicatas(rows, key_fields):
    vistos_linha = set()
    vistos_chave = set()
    indices_duplicados = set()
    duplicatas_linha = 0
    duplicatas_chave = 0

    for index, row in enumerate(rows):
        assinatura = tuple((field, row.get(field, '')) for field in sorted(row))
        if assinatura in vistos_linha:
            duplicatas_linha += 1
            indices_duplicados.add(index)
        else:
            vistos_linha.add(assinatura)

        if key_fields:
            key = tuple(valor_semantico(row.get(field, '')) for field in key_fields)
            if all(part is not None for part in key):
                if key in vistos_chave:
                    duplicatas_chave += 1
                    indices_duplicados.add(index)
                else:
                    vistos_chave.add(key)

    return {
        'duplicatas_unicas': len(indices_duplicados),
        'duplicatas_linha_completa': duplicatas_linha,
        'duplicatas_chave': duplicatas_chave,
        'chave': list(key_fields) if key_fields else ['hash_linha_completa'],
        'linhas_avaliadas': len(rows),
    }


def _try_datetime(value, fmt):
    try:
        datetime.strptime(value, fmt)
        return True
    except ValueError:
        return False


def process_data(input_dir, processado_em=None):
    # Definir timestamps
    if processado_em is None:
        if 'SOURCE_DATE_EPOCH' in os.environ:
            epoch = int(os.environ['SOURCE_DATE_EPOCH'])
            dt = datetime.fromtimestamp(epoch, tz=timezone.utc)
            processado_em = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            processado_em = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    csv_files = {
        'clientes': 'clientes.csv',
        'empresas': 'empresas.csv',
        'pesquisas': 'pesquisas.csv',
        'questoes': 'questoes.csv',
        'respondentes': 'respondentes.csv',
        'respostas': 'teste.csv'
    }

    manifesto_fontes = []
    data_sources = {}

    for file_id in sorted(csv_files.keys()):
        fname = csv_files[file_id]
        fpath = os.path.join(input_dir, fname)
        if not os.path.exists(fpath) and fname == 'teste.csv':
            alt_path = os.path.join(input_dir, 'respostas.csv')
            if os.path.exists(alt_path):
                fpath = alt_path
                fname = 'respostas.csv'

        file_sha = compute_file_sha256(fpath)
        manifesto_fontes.append({
            'arquivo_recebido': fname,
            'id': file_id,
            'sha256': file_sha
        })
        data_sources[file_id] = load_csv(fpath, file_id)

    manifesto_fontes.sort(key=lambda x: x['id'])

    snapshot_json_bytes = json.dumps(
        manifesto_fontes, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    snapshot_sha256 = hashlib.sha256(snapshot_json_bytes).hexdigest()

    pesquisas = data_sources['pesquisas']
    empresas = data_sources['empresas']
    clientes = data_sources['clientes']
    respondentes = data_sources['respondentes']
    questoes = data_sources['questoes']
    teste = data_sources['respostas']

    # --- D01 OPERAÇÃO ---
    total_pesquisas = len(pesquisas)

    data_solicitacao_count = sum(1 for r in pesquisas if r.get('data_solicitacao', '').strip())
    data_aprov_count = sum(1 for r in pesquisas if r.get('data_aprov', '').strip())
    data_divulgacao_count = sum(1 for r in pesquisas if r.get('data_divulgacao', '').strip())
    data_limite_count = sum(1 for r in pesquisas if r.get('data_limite', '').strip())
    prorrogada_ate_count = sum(1 for r in pesquisas if r.get('prorrogada_ate', '').strip())
    data_entrega_count = sum(1 for r in pesquisas if r.get('data_entrega', '').strip())

    i05_pct = round_pct(prorrogada_ate_count, data_limite_count)

    status_finalizadas = sum(1 for r in pesquisas if r.get('status', '').strip() == 'Finalizada')
    status_demais = total_pesquisas - status_finalizadas

    status_detalhados = {}
    for r in pesquisas:
        st = r.get('status', '').strip() or 'Não informado'
        status_detalhados[st] = status_detalhados.get(st, 0) + 1

    comp_alta = sum(1 for r in pesquisas if r.get('complexidade', '').strip() == 'alta')
    comp_media = sum(1 for r in pesquisas if r.get('complexidade', '').strip() == 'média')
    comp_baixa = sum(1 for r in pesquisas if r.get('complexidade', '').strip() == 'baixa')
    comp_nao_inf = sum(1 for r in pesquisas if not r.get('complexidade', '').strip())

    tipo_resp_empresa = sum(1 for r in pesquisas if r.get('tipo de resposta', '').strip() == 'empresa')
    tipo_resp_individuo = sum(1 for r in pesquisas if r.get('tipo de resposta', '').strip() == 'indivíduo')

    solic_por_ano = {'2022': 0, '2023': 0, '2024': 0, '2025': 0, '2026': 0, '2027': 0, 'sem data': 0}
    for r in pesquisas:
        ds = r.get('data_solicitacao', '').strip()
        if not ds:
            solic_por_ano['sem data'] += 1
        else:
            found = False
            for part in ds.replace('/', '-').split('-'):
                if len(part) == 4 and part.isdigit():
                    solic_por_ano[part] = solic_por_ano.get(part, 0) + 1
                    found = True
                    break
            if not found:
                solic_por_ano['sem data'] += 1

    d01_data = {
        'total_pesquisas': total_pesquisas,
        'marcos_temporais': {
            'data_solicitacao': {'preenchidas': data_solicitacao_count, 'total': total_pesquisas},
            'data_aprov': {'preenchidas': data_aprov_count, 'total': total_pesquisas},
            'data_divulgacao': {'preenchidas': data_divulgacao_count, 'total': total_pesquisas},
            'data_limite': {'preenchidas': data_limite_count, 'total': total_pesquisas},
            'prorrogada_ate': {'preenchidas': prorrogada_ate_count, 'total': total_pesquisas},
            'data_entrega': {'preenchidas': data_entrega_count, 'total': total_pesquisas}
        },
        'i05_prorrogacao': {
            'numerador': prorrogada_ate_count,
            'denominador': data_limite_count,
            'percentual': i05_pct,
            'formatado': format_pct(i05_pct)
        },
        'i06_estado': {
            'status': 'indisponivel',
            'motivo': 'Faltam data de referência, elegibilidade de atraso e regra aprovada de prioridade'
        },
        'status_distribuicao': {
            'finalizadas': status_finalizadas,
            'demais': status_demais,
            'detalhes': status_detalhados
        },
        'complexidade_distribuicao': {
            'alta': comp_alta,
            'media': comp_media,
            'baixa': comp_baixa,
            'nao_informado': comp_nao_inf
        },
        'tipo_resposta_distribuicao': {
            'empresa': tipo_resp_empresa,
            'individuo': tipo_resp_individuo
        },
        'solicitacoes_por_ano': solic_por_ano,
        'nota_duracoes': 'Durações de origem ficam separadas de dias corridos.'
    }

    # --- D02 ADESÃO E REPRESENTATIVIDADE ---
    total_participacoes = len(respondentes)
    pesq_ids_pesquisas = set(p['id'].strip() for p in pesquisas if p.get('id', '').strip())
    pesq_ids_resp = set(r.get('id_pesq', '').strip() for r in respondentes if r.get('id_pesq', '').strip())
    emp_ids_resp = set(r.get('id_empresa', '').strip() for r in respondentes if r.get('id_empresa', '').strip())

    vazio_cliente = sum(1 for r in respondentes if not r.get('id_cliente', '').strip())
    si_cliente = sum(1 for r in respondentes if r.get('id_cliente', '').strip().lower() == 's/i')
    sem_cliente_valido = vazio_cliente + si_cliente

    orfas_resp = [r for r in respondentes if r.get('id_pesq', '').strip() not in pesq_ids_pesquisas]
    pesquisas_orfas_resp = {
        r.get('id_pesq', '').strip() for r in orfas_resp if r.get('id_pesq', '').strip()
    }

    from collections import Counter, defaultdict
    empresas_por_pesquisa = defaultdict(set)
    id_empresa_vazios = 0
    for row in respondentes:
        pesquisa_id = valor_semantico(row.get('id_pesq', ''))
        empresa_id = valor_semantico(row.get('id_empresa', ''))
        if empresa_id is None:
            id_empresa_vazios += 1
        elif pesquisa_id is not None:
            empresas_por_pesquisa[pesquisa_id].add(empresa_id)
    val_counts = sorted(len(empresas) for empresas in empresas_por_pesquisa.values())
    n_pesq = len(val_counts)

    def calc_percentile(arr, p):
        if not arr:
            return 0
        idx = int(len(arr) * p)
        return arr[min(idx, len(arr)-1)]

    d02_data = {
        'total_participacoes': total_participacoes,
        'pesquisas_distintas': len(pesq_ids_resp),
        'empresas_distintas': len(emp_ids_resp),
        'id_cliente_sem_valor': sem_cliente_valido,
        'id_cliente_vazios': vazio_cliente,
        'id_cliente_si': si_cliente,
        'id_empresa_vazios': id_empresa_vazios,
        'participacoes_orfas': {
            'total': len(orfas_resp),
            'pesquisas_orfas_distintas': len(pesquisas_orfas_resp)
        },
        'estatisticas_empresas_distintas_por_pesquisa': {
            'min': val_counts[0] if val_counts else 0,
            'q25': calc_percentile(val_counts, 0.25),
            'mediana': calc_percentile(val_counts, 0.50),
            'q75': calc_percentile(val_counts, 0.75),
            'max': val_counts[-1] if val_counts else 0,
            'media': float(Decimal(str(sum(val_counts))) / Decimal(str(n_pesq))) if n_pesq > 0 else 0
        },
        'i08_estado': {
            'status': 'indisponivel',
            'motivo': 'Fonte não contém universo de empresas convidadas ou elegíveis por pesquisa'
        },
        'i11_estado': {
            'status': 'indisponivel',
            'motivo': 'Sem universo elegível por área, cargo ou departamento'
        },
        'i09_diagnostico': {
            'status': 'conflito',
            'descricao': 'Conflito entre market_share e % de mercado; fonte autoritativa não definida',
            'regra': 'sem soma nem precedência presumida'
        }
    }

    # --- D03 RESULTADOS E QUESTIONÁRIOS ---
    total_elementos = len(teste)
    total_questoes = len(questoes)

    respondent_ids_teste = set(r.get('respondent_id', '').strip() for r in teste if r.get('respondent_id', '').strip())
    ids_distintos_fonte = len(respondent_ids_teste)

    tipos_q_counts = Counter(r.get('tipo', '').strip() for r in questoes)

    tipos_questao = {
        'aberta': tipos_q_counts.get('aberta', 0),
        'caixas': tipos_q_counts.get('caixas_de_selecao', 0),
        'matriz': tipos_q_counts.get('matriz_avaliacao', 0),
        'multipla_escolha': tipos_q_counts.get('multipla_escolha', 0),
        'numerica': tipos_q_counts.get('numerica', 0)
    }

    vazio_val = sum(1 for r in teste if not r.get('valor', '').strip())
    na_val = sum(1 for r in teste if r.get('valor', '').strip().upper() == 'NA')

    questoes_orfas = [q for q in questoes if q.get('pesquisa_id', '').strip() not in pesq_ids_pesquisas]
    teste_orfas = [r for r in teste if r.get('pesquisa_id', '').strip() not in pesq_ids_pesquisas]

    # Seleção interna segura do protótipo: somente questões fechadas conhecidas.
    p238_q110_rows = [r for r in teste if r.get('pesquisa_id', '').strip() == '238' and r.get('id_pergunta', '').strip() == '110']
    q110_val_counts = Counter(r.get('valor', '').strip() for r in p238_q110_rows if r.get('valor', '').strip())
    q110_sim = q110_val_counts.get('Sim', 0)
    q110_nao = q110_val_counts.get('Não', 0)
    q110_total = q110_sim + q110_nao

    p238_q104_rows = [r for r in teste if r.get('pesquisa_id', '').strip() == '238' and r.get('id_pergunta', '').strip() == '104']
    q104_alt_counts = Counter(r.get('alternativa', '').strip() for r in p238_q104_rows if r.get('alternativa', '').strip())
    q104_total_selecoes = sum(q104_alt_counts.values())

    q104_distribuicao = []
    ordem_q104 = ['Diretores', 'Colaboradores de Campo', 'Presidente', 'Gerentes', 'Gerentes Sr.', 'Vice-presidente']
    for opt in ordem_q104:
        qtd = q104_alt_counts.get(opt, 0)
        pct = round_pct(qtd, q104_total_selecoes)
        q104_distribuicao.append({
            'opcao': opt,
            'quantidade': qtd,
            'numerador': qtd,
            'denominador': q104_total_selecoes,
            'percentual': pct,
            'formatado': format_pct(pct)
        })

    tipos_por_questao = {
        (q.get('pesquisa_id', '').strip(), q.get('id_pergunta', '').strip()): q.get('tipo', '').strip()
        for q in questoes
    }
    respostas_matriz = [
        r for r in teste
        if tipos_por_questao.get((r.get('pesquisa_id', '').strip(), r.get('id_pergunta', '').strip())) == 'matriz_avaliacao'
    ]
    matriz_ausencias = sum(
        1 for r in respostas_matriz
        if not r.get('linha_matriz', '').strip() or not r.get('coluna_matriz', '').strip()
    )

    d03_data = {
        'total_elementos': total_elementos,
        'total_questoes': total_questoes,
        'ids_distintos_fonte': ids_distintos_fonte,
        'tipos_questao': tipos_questao,
        'valores_vazios_ou_na': {
            'vazios': vazio_val,
            'na': na_val,
            'total': vazio_val + na_val
        },
        'pesquisas_orfas_count': len(set(q.get('pesquisa_id', '').strip() for q in questoes_orfas)),
        'elementos_orfaos_count': len(teste_orfas),
        'questoes_orfas_count': len(questoes_orfas),
        'matrizes': {
            'ausencias_inesperadas': matriz_ausencias,
            'aplicaveis': len(respostas_matriz)
        },
        'exemplos_selecionados': [
            {
                'codigo_exemplo': 'A',
                'tipo': 'multipla_escolha',
                'validos': q110_total,
                'distribuicao': [
                    {
                        'opcao': 'Sim',
                        'quantidade': q110_sim,
                        'numerador': q110_sim,
                        'denominador': q110_total,
                        'percentual': round_pct(q110_sim, q110_total),
                        'formatado': format_pct(round_pct(q110_sim, q110_total))
                    },
                    {
                        'opcao': 'Não',
                        'quantidade': q110_nao,
                        'numerador': q110_nao,
                        'denominador': q110_total,
                        'percentual': round_pct(q110_nao, q110_total),
                        'formatado': format_pct(round_pct(q110_nao, q110_total))
                    }
                ]
            },
            {
                'codigo_exemplo': 'B',
                'tipo': 'caixas',
                'total_selecoes': q104_total_selecoes,
                'nota_denominador': 'Denominador é total de seleções (299), não respondentes.',
                'distribuicao': q104_distribuicao
            }
        ]
    }

    # --- D04 QUALIDADE E GOVERNANÇA ---
    total_linhas_fontes = sum(len(v) for v in data_sources.values())
    duplicatas_por_fonte = {
        source_id: perfil_duplicatas(rows, CHAVES_CANDIDATAS[source_id])
        for source_id, rows in data_sources.items()
    }
    total_duplicatas = sum(
        profile['duplicatas_unicas'] for profile in duplicatas_por_fonte.values()
    )

    resp_encontradas = total_participacoes - len(orfas_resp)
    resp_pct = round_pct(resp_encontradas, total_participacoes)

    questoes_encontradas = total_questoes - len(questoes_orfas)
    questoes_pct = round_pct(questoes_encontradas, total_questoes)

    respostas_encontradas = total_elementos - len(teste_orfas)
    respostas_pct = round_pct(respostas_encontradas, total_elementos)

    q_ids_questoes = set(q['id_pergunta'].strip() for q in questoes)
    respostas_com_q = sum(1 for r in teste if r.get('id_pergunta', '').strip() in q_ids_questoes)
    respostas_q_pct = round_pct(respostas_com_q, total_elementos)

    pesq_dict = {p['id'].strip(): p.get('titulo', '').strip() for p in pesquisas}
    valid_qs = [q for q in questoes if q.get('pesquisa_id', '').strip() in pesq_dict]
    divergencias_titulos = sum(1 for q in valid_qs if q.get('pesquisa_titulo', '').strip() != pesq_dict[q.get('pesquisa_id', '').strip()])
    div_titulos_pct = round_pct(divergencias_titulos, len(valid_qs))

    especificacoes_parseabilidade = [
        (pesquisas, 'pesquisas', field, 'data', ['%d/%m/%Y'])
        for field in ['data_solicitacao', 'data_aprov', 'data_divulgacao', 'data_limite', 'prorrogada_ate', 'data_entrega']
    ] + [
        (respondentes, 'respondentes', field, 'data', ['%d/%m/%Y %H:%M'])
        for field in ['hora_inicio', 'hora_termino']
    ] + [
        (pesquisas, 'pesquisas', 'part_mercado', 'percentual', None),
        (empresas, 'empresas', '% de mercado', 'percentual', None),
        (respondentes, 'respondentes', 'market_share', 'percentual', None),
    ] + [
        (source_rows, source_id, field, 'inteiro', None)
        for source_rows, source_id, fields in [
            (pesquisas, 'pesquisas', ['id', 'participantes', 'dias_uteis_para_entrega', 'tempo_preenchimento', 'dias úteis aberta', 'dias entre a solicitação e a divulgação', 'dias para tabulação']),
            (empresas, 'empresas', ['ID']),
            (clientes, 'clientes', ['id_cliente', 'id_empresa']),
            (respondentes, 'respondentes', ['id_pesq', 'id_empresa', 'id_cliente']),
            (questoes, 'questoes', ['id_pergunta', 'pesquisa_id', 'qtd_alternativas']),
            (teste, 'respostas', ['id_resposta', 'pesquisa_id', 'id_pergunta', 'respondent_id', 'id_empresa']),
        ]
        for field in fields
    ]
    parseabilidade_por_campo = []
    for rows, source_id, field, kind, formats in especificacoes_parseabilidade:
        profile = perfil_parseabilidade(rows, field, kind, formats)
        profile['fonte'] = source_id
        parseabilidade_por_campo.append(profile)
    valores_parseaveis = sum(profile['validos'] for profile in parseabilidade_por_campo)
    valores_avaliados = sum(profile['avaliados'] for profile in parseabilidade_por_campo)

    d04_data = {
        'total_linhas_fontes': total_linhas_fontes,
        'total_duplicatas': total_duplicatas,
        'duplicatas_por_fonte': duplicatas_por_fonte,
        'parseabilidade_por_campo': parseabilidade_por_campo,
        'integridade': {
            'respondentes_para_pesquisas': {
                'numerador': resp_encontradas,
                'denominador': total_participacoes,
                'orfas': len(orfas_resp),
                'percentual': resp_pct,
                'formatado': format_pct(resp_pct)
            },
            'questoes_para_pesquisas': {
                'numerador': questoes_encontradas,
                'denominador': total_questoes,
                'orfas': len(questoes_orfas),
                'percentual': questoes_pct,
                'formatado': format_pct(questoes_pct)
            },
            'respostas_para_pesquisas': {
                'numerador': respostas_encontradas,
                'denominador': total_elementos,
                'orfas': len(teste_orfas),
                'percentual': respostas_pct,
                'formatado': format_pct(respostas_pct)
            },
            'respostas_para_questoes': {
                'numerador': respostas_com_q,
                'denominador': total_elementos,
                'orfas': 0,
                'percentual': respostas_q_pct,
                'formatado': format_pct(respostas_q_pct)
            }
        },
        'divergencia_titulos': {
            'numerador': divergencias_titulos,
            'denominador': len(valid_qs),
            'percentual': div_titulos_pct,
            'formatado': format_pct(div_titulos_pct)
        },
        'matriz_regras_i16_i20': [
            {
                'id_regra': 'I16',
                'nome': 'Completude aplicável da matriz',
                'numerador': len(respostas_matriz) - matriz_ausencias,
                'denominador': len(respostas_matriz),
                'percentual': round_pct(len(respostas_matriz) - matriz_ausencias, len(respostas_matriz)),
                'formatado': format_pct(round_pct(len(respostas_matriz) - matriz_ausencias, len(respostas_matriz))),
                'status': 'divergencia_observada' if matriz_ausencias else 'conforme',
                'descricao': f'{matriz_ausencias} ausências inesperadas em {len(respostas_matriz)} elementos de matriz aplicáveis.'
            },
            {
                'id_regra': 'I17',
                'nome': 'Taxa de duplicidade',
                'numerador': total_duplicatas,
                'denominador': total_linhas_fontes,
                'percentual': round_pct(total_duplicatas, total_linhas_fontes),
                'formatado': format_pct(round_pct(total_duplicatas, total_linhas_fontes)),
                'status': 'divergencia_observada' if total_duplicatas else 'conforme',
                'descricao': f'{total_duplicatas} linhas além da primeira por linha completa ou chave candidata; cada linha é contada uma vez.'
            },
            *[
                {
                    'id_regra': 'I18',
                    'nome': name,
                    'numerador': relationship['numerador'],
                    'denominador': relationship['denominador'],
                    'percentual': relationship['percentual'],
                    'formatado': relationship['formatado'],
                    'status': 'divergencia_observada' if relationship['orfas'] else 'conforme',
                    'descricao': f"{relationship['orfas']} ocorrências órfãs na relação avaliada.",
                }
                for name, relationship in [
                    ('Integridade: participações → pesquisas', {
                        'numerador': resp_encontradas,
                        'denominador': total_participacoes,
                        'orfas': len(orfas_resp),
                        'percentual': resp_pct,
                        'formatado': format_pct(resp_pct),
                    }),
                    ('Integridade: questões → pesquisas', {
                        'numerador': questoes_encontradas,
                        'denominador': total_questoes,
                        'orfas': len(questoes_orfas),
                        'percentual': questoes_pct,
                        'formatado': format_pct(questoes_pct),
                    }),
                    ('Integridade: respostas → pesquisas', {
                        'numerador': respostas_encontradas,
                        'denominador': total_elementos,
                        'orfas': len(teste_orfas),
                        'percentual': respostas_pct,
                        'formatado': format_pct(respostas_pct),
                    }),
                ]
            ],
            {
                'id_regra': 'I19',
                'nome': 'Parseabilidade dos valores configurados',
                'numerador': valores_parseaveis,
                'denominador': valores_avaliados,
                'percentual': round_pct(valores_parseaveis, valores_avaliados),
                'formatado': format_pct(round_pct(valores_parseaveis, valores_avaliados)),
                'status': 'conforme' if valores_parseaveis == valores_avaliados else 'divergencia_observada',
                'descricao': f'{len(parseabilidade_por_campo)} campos temporais, percentuais e inteiros; a unidade é valor semanticamente informado.'
            },
            {
                'id_regra': 'I20',
                'nome': 'Divergência de títulos registrados',
                'numerador': divergencias_titulos,
                'denominador': len(valid_qs),
                'percentual': div_titulos_pct,
                'formatado': format_pct(div_titulos_pct),
                'status': 'divergencia_observada',
                'descricao': f'{divergencias_titulos} linhas de questão divergentes entre {len(valid_qs)} comparáveis.'
            }
        ],
        'i21_estado': {
            'status': 'indisponivel',
            'motivo': 'Métrica não calculada na carga atual'
        },
        'i22_estado': {
            'status': 'sem_percentual',
            'valor': 'Evidência parcial; percentual indisponível até definir elos elegíveis'
        },
        'i23_estado': {
            'status': 'indisponivel',
            'motivo': 'Autorização, estado e data de publicação não existem no snapshot'
        },
        'i24_estado': {
            'status': 'indisponivel',
            'motivo': 'Catálogo de fontes esperadas e execuções de ingestão não existem no snapshot'
        },
        'i25_estado': {
            'status': 'indisponivel',
            'motivo': 'Política aprovada e logs de autorização não existem no snapshot'
        },
        'fluxo_textual': {
            'observado': 'Fluxo observado: seis arquivos CSV recebidos, identificados por hash SHA-256 e processados sem alterar os originais.',
            'em_reconciliacao': 'Fluxo em reconciliação: relações órfãs permanecem separadas e a ponte entre participação e resposta não foi comprovada.',
            'proposto': 'Fluxo proposto: integrar catálogo, sistema de origem, execuções e regras aprovadas antes de calcular a cobertura da linhagem.'
        }
    }

    output_data = {
        'versao_schema': '1.0.0',
        'processado_em': processado_em,
        'nota_frescor': 'A data de processamento registra o momento da execução do pipeline e não mede o frescor dos dados de origem.',
        'snapshot_sha256': snapshot_sha256,
        'manifesto_fontes': manifesto_fontes,
        'd01_operacao': d01_data,
        'd02_adesao': d02_data,
        'd03_resultados': d03_data,
        'd04_qualidade': d04_data
    }

    return output_data


def main():
    parser = argparse.ArgumentParser(description="Gerador de dados agregados para protótipos de dashboard.")
    parser.add_argument("--input-dir", required=True, help="Diretório das seis fontes CSV")
    parser.add_argument("--output", default="dados-dashboard.json", help="Arquivo JSON de saída")
    parser.add_argument("--processado-em", default=None, help="Timestamp ISO 8601 explícito para reprodutibilidade")

    args = parser.parse_args()

    try:
        output_data = process_data(args.input_dir, args.processado_em)

        tmp_output = args.output + ".tmp"
        with open(tmp_output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")

        os.replace(tmp_output, args.output)
        print(f"Sucesso: Dados gerados com sucesso em {args.output}")
    except Exception as e:
        print(f"Erro ao gerar dados: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
