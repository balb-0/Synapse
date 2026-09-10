"""Canário do acoplamento entre a deduplicação e o contrato físico da carga.

Se um teste deste arquivo falhar, a semântica de identidade mudou em uma das
duas pontas. **Não conserte o teste sem ler**
``docs/adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md``: as duas
mudanças precisam andar juntas, senão o reprocessamento explícito passa a
violar a chave primária da tabela de ingestão e derruba o lote inteiro.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from etl.load.ddl import CONTROL_STATEMENTS  # noqa: E402
from etl.transformation.identity import classify_duplicates  # noqa: E402

ADR = "docs/adrs/0002-identidade-e-versoes-na-tabela-de-ingestao.md"

MUDOU_A_CLASSIFICACAO = (
    "A deduplicação passou a aceitar correção do parceiro como versão nova. "
    f"Antes de ajustar este teste, confira em {ADR} que a tabela de controle "
    "`_loaded_identity` foi rechaveada pela identidade de idempotência. Sem "
    "isso, um backfill com reprocesso classifica uma versão antiga como aceita "
    "e a carga viola a chave primária da tabela de ingestão."
)

MUDOU_O_CONTROLE = (
    "A tabela de controle `_loaded_identity` deixou de ser chaveada pela "
    "identidade da chave de negócio. Se a intenção é aceitar versões, a "
    "classificação de duplicidade precisa mudar junto; se não é, o controle "
    f"ficou incoerente com a comparação. Ver {ADR}."
)


class IdentityCouplingCanaryTests(unittest.TestCase):
    def test_corrected_record_is_still_rejected_by_the_previous_layer(self) -> None:
        outcomes = classify_duplicates(
            [("identidade-424", "conteudo-corrigido")],
            {"identidade-424": "conteudo-original"},
        )

        self.assertEqual(outcomes, ["conflict"], MUDOU_A_CLASSIFICACAO)

    def test_identical_reload_is_still_a_duplicate(self) -> None:
        outcomes = classify_duplicates(
            [("identidade-424", "conteudo-original")],
            {"identidade-424": "conteudo-original"},
        )

        self.assertEqual(outcomes, ["duplicate"], MUDOU_A_CLASSIFICACAO)

    def test_contradiction_inside_the_same_batch_stays_a_conflict(self) -> None:
        # Este caso permanece rejeitado nas duas semânticas: é contradição do
        # próprio arquivo, não correção entre execuções.
        outcomes = classify_duplicates(
            [("identidade-424", "conteudo-a"), ("identidade-424", "conteudo-b")], {}
        )

        self.assertEqual(outcomes, ["conflict", "conflict"])

    def test_control_table_is_still_keyed_by_the_business_identity(self) -> None:
        loaded_identity = next(
            statement for statement in CONTROL_STATEMENTS if "_loaded_identity" in statement
        )

        self.assertIn("record_identity VARCHAR PRIMARY KEY", loaded_identity, MUDOU_O_CONTROLE)


if __name__ == "__main__":
    unittest.main()
