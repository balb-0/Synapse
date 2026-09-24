"""Serialização estruturada dos logs em JSON (OB-03).

As quatro etapas já publicam eventos técnicos com o nome do evento como
mensagem e os atributos de correlação em ``extra`` do ``logging`` padrão —
mas isso ainda vivia só como ``LogRecord`` em memória, sem nenhum formatter
que o transformasse em texto JSON de verdade. Este módulo fecha essa lacuna:
``StructuredJsonFormatter`` serializa qualquer registro (nosso ou de
terceiros, como os logs internos do próprio Prefect) e
``configure_json_logging`` liga esse formatter aos loggers onde os eventos
das quatro etapas realmente aparecem.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import TextIO

OBSERVED_LOGGERS = (
    "etl.extraction",
    "etl.transformation",
    "etl.load",
    "prefect.task_runs",
    "prefect.flow_runs",
)

_RESERVED_RECORD_KEYS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", (), None)))


class StructuredJsonFormatter(logging.Formatter):
    """Formata um ``LogRecord`` como uma linha JSON.

    Não assume nada sobre quais atributos técnicos existem — copia todo
    atributo que não é bookkeeping padrão do ``LogRecord`` (ou seja, tudo
    que chegou via ``extra``). Isso faz o formatter servir extração,
    transformação, carga, orquestração e qualquer evento futuro sem precisar
    conhecer o formato de cada um.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _RESERVED_RECORD_KEYS:
                payload[key] = value
        return json.dumps(payload, default=str, ensure_ascii=False)


def configure_json_logging(*, stream: TextIO | None = None, level: int = logging.INFO) -> None:
    """Liga o formatter JSON aos loggers das quatro etapas.

    Só adiciona um handler — não mexe nos que já existem. O Prefect já anexa
    o próprio ``APILogHandler`` a ``prefect.task_runs``/``prefect.flow_runs``
    para alimentar o histórico de execução da sua UI (OQ-02/OQ-03); remover
    isso quebraria esse histórico sem necessidade. O console colorido que o
    Prefect imprime para acompanhamento humano vai para o `stderr`
    (`PrefectConsoleHandler`, anexado no logger raiz) — canal diferente do
    `stdout`, que é de onde o Logstash coleta (ADR 0001). Não há colisão real
    a resolver: os dois streams já convivem sem se misturar.

    Idempotente: chamar mais de uma vez (o runner reexecuta o script, os
    testes reconfiguram entre casos) não duplica handler no mesmo logger.
    ``stream`` é injetável para teste; em produção é ``sys.stdout``.
    """
    target_stream = stream if stream is not None else sys.stdout
    for logger_name in OBSERVED_LOGGERS:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        already_configured = any(
            isinstance(handler.formatter, StructuredJsonFormatter) for handler in logger.handlers
        )
        if already_configured:
            continue
        handler = logging.StreamHandler(target_stream)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
