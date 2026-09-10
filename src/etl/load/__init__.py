"""Carga dos dados tratados no banco de ingestão local em DuckDB.

Este pacote não reexporta seus módulos de propósito. O ``__init__`` de um
pacote roda antes de qualquer submódulo, então uma fachada aqui tornaria o
``duckdb`` obrigatório até para importar ``etl.load.config`` — e é a ausência
dessa exigência que permite exercitar a configuração em ambientes que não
instalam o driver. Importe de ``etl.load.config`` e ``etl.load.environment``.
"""
