#!/usr/bin/env python3
"""
test_gerar_dados_prototipos.py

Testes unitários para validar a geração determinística de dados dos protótipos
de dashboard do Sindusfarma/Central de Pesquisas.
"""

import os
import sys
import json
import math
import hashlib
import unittest
import tempfile
import importlib.util
from pathlib import Path

# Importar o módulo gerador
GENERATOR_PATH = os.path.join(os.path.dirname(__file__), "gerar-dados-prototipos.py")
spec = importlib.util.spec_from_file_location("gerar_dados_prototipos", GENERATOR_PATH)
gerar_dados_prototipos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gerar_dados_prototipos)


class TestGeradorDadosPrototipos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        default_input = Path(__file__).resolve().parents[5] / "context" / "csv"
        cls.input_dir = os.environ.get("SINDUSFARMA_CSV_DIR", str(default_input))
        if not Path(cls.input_dir).is_dir():
            raise unittest.SkipTest(
                "Fontes CSV ausentes; informe SINDUSFARMA_CSV_DIR para executar os testes de integração."
            )
        cls.fixed_timestamp = "2026-08-13T00:00:00Z"
        cls.data = gerar_dados_prototipos.process_data(cls.input_dir, cls.fixed_timestamp)

    def test_schema_e_cabecalhos(self):
        """Valida a presença de campos obrigatórios no topo do schema."""
        self.assertEqual(self.data.get('versao_schema'), '1.0.0')
        self.assertEqual(self.data.get('processado_em'), self.fixed_timestamp)
        self.assertIn('snapshot_sha256', self.data)
        self.assertIn('manifesto_fontes', self.data)
        self.assertEqual(len(self.data['manifesto_fontes']), 6)
        respostas = next(f for f in self.data['manifesto_fontes'] if f['id'] == 'respostas')
        self.assertEqual(respostas['arquivo_recebido'], 'teste.csv')
        self.assertFalse(any(f['id'] == 'teste' for f in self.data['manifesto_fontes']))

    def test_arquivo_ausente_lanca_erro(self):
        """Valida que o gerador falha explicitamente se um CSV estiver ausente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(FileNotFoundError):
                gerar_dados_prototipos.process_data(tmpdir, self.fixed_timestamp)

    def test_golden_numbers_d01(self):
        """Valida os números já verificados do D01."""
        d01 = self.data['d01_operacao']
        self.assertEqual(d01['total_pesquisas'], 366)
        
        marcos = d01['marcos_temporais']
        self.assertEqual(marcos['data_solicitacao']['preenchidas'], 362)
        self.assertEqual(marcos['data_aprov']['preenchidas'], 20)
        self.assertEqual(marcos['data_divulgacao']['preenchidas'], 358)
        self.assertEqual(marcos['data_limite']['preenchidas'], 358)
        self.assertEqual(marcos['prorrogada_ate']['preenchidas'], 68)
        self.assertEqual(marcos['data_entrega']['preenchidas'], 334)

        i05 = d01['i05_prorrogacao']
        self.assertEqual(i05['numerador'], 68)
        self.assertEqual(i05['denominador'], 358)
        self.assertEqual(i05['percentual'], 19.0)
        self.assertEqual(i05['formatado'], '19,0%')

        status = d01['status_distribuicao']
        self.assertEqual(status['finalizadas'], 332)
        self.assertEqual(status['demais'], 34)

        comp = d01['complexidade_distribuicao']
        self.assertEqual(comp['alta'], 53)
        self.assertEqual(comp['media'], 27)
        self.assertEqual(comp['baixa'], 10)
        self.assertEqual(comp['nao_informado'], 276)

        tipo_resp = d01['tipo_resposta_distribuicao']
        self.assertEqual(tipo_resp['empresa'], 342)
        self.assertEqual(tipo_resp['individuo'], 24)

        anos = d01['solicitacoes_por_ano']
        self.assertEqual(anos['2022'], 5)
        self.assertEqual(anos['2023'], 95)
        self.assertEqual(anos['2024'], 99)
        self.assertEqual(anos['2025'], 119)
        self.assertEqual(anos['2026'], 41)
        self.assertEqual(anos['2027'], 3)
        self.assertEqual(anos['sem data'], 4)

        self.assertEqual(d01['i06_estado']['status'], 'indisponivel')

    def test_golden_numbers_d02(self):
        """Valida os números já verificados do D02."""
        d02 = self.data['d02_adesao']
        self.assertEqual(d02['total_participacoes'], 18735)
        self.assertEqual(d02['pesquisas_distintas'], 327)
        self.assertEqual(d02['empresas_distintas'], 419)
        
        self.assertEqual(d02['id_cliente_sem_valor'], 857)
        self.assertEqual(d02['id_cliente_vazios'], 856)
        self.assertEqual(d02['id_cliente_si'], 1)

        orfas = d02['participacoes_orfas']
        self.assertEqual(orfas['total'], 55)
        self.assertEqual(orfas['pesquisas_orfas_distintas'], 1)

        self.assertEqual(d02['i08_estado']['status'], 'indisponivel')
        self.assertEqual(d02['i11_estado']['status'], 'indisponivel')
        self.assertEqual(d02['i09_diagnostico']['status'], 'conflito')

    def test_golden_numbers_d03(self):
        """Valida os números já verificados do D03."""
        d03 = self.data['d03_resultados']
        self.assertEqual(d03['total_elementos'], 20607)
        self.assertEqual(d03['total_questoes'], 231)
        self.assertEqual(d03['ids_distintos_fonte'], 542)

        tipos = d03['tipos_questao']
        self.assertEqual(tipos['aberta'], 4)
        self.assertEqual(tipos['caixas'], 80)
        self.assertEqual(tipos['matriz'], 3)
        self.assertEqual(tipos['multipla_escolha'], 123)
        self.assertEqual(tipos['numerica'], 21)

        val_null = d03['valores_vazios_ou_na']
        self.assertEqual(val_null['vazios'], 8307)
        self.assertEqual(val_null['na'], 2)
        self.assertEqual(val_null['total'], 8309)

        self.assertEqual(d03['pesquisas_orfas_count'], 4)
        self.assertEqual(d03['elementos_orfaos_count'], 3592)
        self.assertEqual(d03['questoes_orfas_count'], 43)

        matriz = d03['matrizes']
        self.assertEqual(matriz['ausencias_inesperadas'], 4)
        self.assertEqual(matriz['aplicaveis'], 4008)

        # Seleção fechada com rótulos neutros; IDs de origem não saem no snapshot.
        exs = d03['exemplos_selecionados']
        self.assertEqual(len(exs), 2)
        
        q110 = next(e for e in exs if e['codigo_exemplo'] == 'A')
        self.assertEqual(q110['validos'], 58)
        dist_110 = {d['opcao']: d['quantidade'] for d in q110['distribuicao']}
        self.assertEqual(dist_110['Sim'], 50)
        self.assertEqual(dist_110['Não'], 8)

        q104 = next(e for e in exs if e['codigo_exemplo'] == 'B')
        self.assertEqual(q104['total_selecoes'], 299)
        dist_104 = [d['quantidade'] for d in q104['distribuicao']]
        self.assertEqual(dist_104, [56, 55, 52, 50, 48, 38])

    def test_golden_numbers_d04(self):
        """Valida os números já verificados do D04."""
        d04 = self.data['d04_qualidade']
        self.assertEqual(d04['total_linhas_fontes'], 46148)
        self.assertEqual(d04['total_duplicatas'], 0)

        integ = d04['integridade']
        self.assertEqual(integ['respondentes_para_pesquisas']['numerador'], 18680)
        self.assertEqual(integ['respondentes_para_pesquisas']['denominador'], 18735)
        self.assertEqual(integ['respondentes_para_pesquisas']['orfas'], 55)

        self.assertEqual(integ['questoes_para_pesquisas']['numerador'], 188)
        self.assertEqual(integ['questoes_para_pesquisas']['denominador'], 231)
        self.assertEqual(integ['questoes_para_pesquisas']['orfas'], 43)

        self.assertEqual(integ['respostas_para_pesquisas']['numerador'], 17015)
        self.assertEqual(integ['respostas_para_pesquisas']['denominador'], 20607)
        self.assertEqual(integ['respostas_para_pesquisas']['orfas'], 3592)

        self.assertEqual(integ['respostas_para_questoes']['numerador'], 20607)
        self.assertEqual(integ['respostas_para_questoes']['denominador'], 20607)
        self.assertEqual(integ['respostas_para_questoes']['orfas'], 0)

        div_tit = d04['divergencia_titulos']
        self.assertEqual(div_tit['numerador'], 41)
        self.assertEqual(div_tit['denominador'], 188)
        self.assertEqual(div_tit['percentual'], 21.8)
        self.assertEqual(div_tit['formatado'], '21,8%')

        regras = {r['id_regra']: r for r in d04['matriz_regras_i16_i20']}
        self.assertEqual(set(regras), {'I16', 'I17', 'I18', 'I19', 'I20'})
        self.assertEqual((regras['I16']['numerador'], regras['I16']['denominador']), (4004, 4008))
        self.assertEqual((regras['I17']['numerador'], regras['I17']['denominador']), (0, 46148))
        self.assertEqual((regras['I18']['numerador'], regras['I18']['denominador']), (35883, 39573))
        self.assertEqual((regras['I20']['numerador'], regras['I20']['denominador']), (41, 188))

        self.assertEqual(d04['i21_estado']['status'], 'indisponivel')
        self.assertEqual(d04['i22_estado']['status'], 'sem_percentual')
        self.assertEqual(d04['i23_estado']['status'], 'indisponivel')
        self.assertEqual(d04['i24_estado']['status'], 'indisponivel')
        self.assertEqual(d04['i25_estado']['status'], 'indisponivel')

    def test_invariantes(self):
        """Valida invariantes fundamentais (soma, numerador <= denominador, found+orphan=total)."""
        d01 = self.data['d01_operacao']
        comp = d01['complexidade_distribuicao']
        self.assertEqual(comp['alta'] + comp['media'] + comp['baixa'] + comp['nao_informado'], d01['total_pesquisas'])

        status = d01['status_distribuicao']
        self.assertEqual(status['finalizadas'] + status['demais'], d01['total_pesquisas'])

        d03 = self.data['d03_resultados']
        tipos = d03['tipos_questao']
        self.assertEqual(sum(tipos.values()), d03['total_questoes'])

        d04 = self.data['d04_qualidade']
        for k, v in d04['integridade'].items():
            self.assertLessEqual(v['numerador'], v['denominador'])
            self.assertEqual(v['numerador'] + v['orfas'], v['denominador'])

    def test_determinismo(self):
        """Valida se execuções repetidas geram saída byte a byte idêntica."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "out1.json")
            file2 = os.path.join(tmpdir, "out2.json")

            data1 = gerar_dados_prototipos.process_data(self.input_dir, self.fixed_timestamp)
            with open(file1, "w", encoding="utf-8") as f:
                json.dump(data1, f, ensure_ascii=False, indent=2, sort_keys=True)
                f.write("\n")

            data2 = gerar_dados_prototipos.process_data(self.input_dir, self.fixed_timestamp)
            with open(file2, "w", encoding="utf-8") as f:
                json.dump(data2, f, ensure_ascii=False, indent=2, sort_keys=True)
                f.write("\n")

            with open(file1, "rb") as f1, open(file2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())

    def test_privacidade_por_lista_de_bloqueio_recursiva(self):
        """Valida que nenhum dado pessoal/identificador individual vazou no JSON."""
        forbidden_keys = {
            'email', 'e-mail', 'nome_fantasia', 'id_cliente', 'respondent_id',
            'id_resposta', 'id_empresa', 'pesquisa_id', 'id_pergunta'
        }

        def check_node(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    self.assertNotIn(k.lower(), forbidden_keys, f"Chave proibida encontrada no JSON: {k}")
                    check_node(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_node(item)
            elif isinstance(obj, str):
                self.assertNotIn('@', obj, f"Formato de e-mail detectado em valor de texto: {obj}")

        check_node(self.data)

    def test_ausencia_nan_infinity(self):
        """Garante que não existem valores NaN ou Infinity no JSON gerado."""
        def check_numeric(obj):
            if isinstance(obj, float):
                self.assertFalse(math.isnan(obj), "Valor NaN encontrado no JSON")
                self.assertFalse(math.isinf(obj), "Valor Infinity encontrado no JSON")
            elif isinstance(obj, dict):
                for v in obj.values():
                    check_numeric(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_numeric(item)

        check_numeric(self.data)

    def test_taxas_possuem_denominador(self):
        """Garante que todas as taxas percentuais no JSON possuem denominador preenchido e > 0."""
        def check_taxa(obj):
            if isinstance(obj, dict):
                if 'percentual' in obj and obj['percentual'] is not None:
                    self.assertIn('denominador', obj)
                    self.assertIsNotNone(obj['denominador'])
                    self.assertGreater(obj['denominador'], 0)
                for v in obj.values():
                    check_taxa(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_taxa(item)

        check_taxa(self.data)

    def test_hashes_e_snapshot(self):
        """Valida o cálculo dos hashes individuais e do snapshot_sha256."""
        manifesto = self.data['manifesto_fontes']
        self.assertEqual(len(manifesto), 6)
        
        # Snapshot SHA256 spec validation
        snapshot_json_bytes = json.dumps(
            manifesto, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        ).encode('utf-8')
        expected_snapshot_hash = hashlib.sha256(snapshot_json_bytes).hexdigest()
        
        self.assertEqual(self.data['snapshot_sha256'], expected_snapshot_hash)


if __name__ == "__main__":
    unittest.main()
