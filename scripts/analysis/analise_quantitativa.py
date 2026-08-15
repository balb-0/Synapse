#!/usr/bin/env python3
"""Calcula agregados quantitativos do snapshot sem expor dados brutos."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median, stdev


SOURCES = {
    "pesquisas": (("pesquisas.csv",), ["id", "data_divulgacao"]),
    "empresas": (("empresas.csv",), ["ID"]),
    "clientes": (("clientes.csv", "clientes (1).csv"), ["id_cliente"]),
    "respondentes": (("respondentes.csv",), ["id_pesq", "id_empresa"]),
    "questoes": (("questoes.csv", "questoes (2).csv"), ["id_pergunta", "pesquisa_id"]),
    "respostas": (("respostas.csv", "teste.csv"), ["id_resposta", "pesquisa_id", "respondent_id"]),
}
DATE_FORMATS = ("%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d")
MONTH_LABELS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]


def clean(value: str | None) -> str:
    return (value or "").strip()


def number(value: str | None) -> float | None:
    text = clean(value).replace("%", "").replace(" ", "")
    if not text:
        return None
    try:
        return float(text.replace(".", "").replace(",", "."))
    except ValueError:
        return None


def date(value: str | None) -> datetime | None:
    text = clean(value)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def pct(value: int | float, total: int | float) -> str:
    return "indisponível" if not total else f"{value * 100 / total:.1f}%".replace(".", ",")


def read_csv(path: Path, required: list[str]) -> list[dict[str, str]]:
    if not path.is_file():
        raise ValueError(f"fonte ausente: {path.name}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        fields = reader.fieldnames or []
        missing = [field for field in required if field not in fields]
        if missing:
            raise ValueError(f"{path.name}: colunas ausentes: {', '.join(missing)}")
        return [{key: clean(value) for key, value in row.items() if key is not None} for row in reader]


def load_sources(root: Path) -> tuple[dict[str, list[dict[str, str]]], dict[str, str]]:
    data: dict[str, list[dict[str, str]]] = {}
    hashes: dict[str, str] = {}
    for source, (filenames, required) in SOURCES.items():
        path = next((root / filename for filename in filenames if (root / filename).is_file()), root / filenames[0])
        data[source] = read_csv(path, required)
        hashes[source] = hashlib.sha256(path.read_bytes()).hexdigest()
    return data, hashes


def calculate(data: dict[str, list[dict[str, str]]]) -> dict[str, object]:
    researches = data["pesquisas"]
    by_research = {clean(row["id"]): row for row in researches if clean(row["id"])}
    published = [(row, date(row.get("data_divulgacao"))) for row in researches]
    dated = [(row, day) for row, day in published if day]
    years = Counter(day.year for _, day in dated)
    months = Counter(day.month for _, day in dated)
    weekdays = Counter(clean(row.get("dia da semana de lançamento")) for row, _ in published)
    valid_weekdays = [(row, day) for row, day in dated if clean(row.get("dia da semana de lançamento")) not in {"", "7"}]
    weekday_matches = sum(int(int(row["dia da semana de lançamento"]) == day.weekday() + 2) for row, day in valid_weekdays)

    cycle_by_year: dict[int, list[float]] = defaultdict(list)
    cycle_all: list[float] = []
    extension_by_year: Counter[int] = Counter()
    for row, day in dated:
        cycle = number(row.get("dias_uteis_para_entrega"))
        if cycle is not None:
            cycle_all.append(cycle)
            cycle_by_year[day.year].append(cycle)
        if date(row.get("prorrogada_ate")):
            extension_by_year[day.year] += 1

    respondents = data["respondentes"]
    participation_year: dict[int, dict[str, object]] = defaultdict(lambda: {"records": 0, "companies": set(), "people": set()})
    observed_companies: dict[str, set[str]] = defaultdict(set)
    for row in respondents:
        rid = clean(row.get("id_pesq"))
        observed_companies[rid].add(clean(row.get("id_empresa")))
        research_day = date(by_research.get(rid, {}).get("data_divulgacao"))
        if not research_day:
            continue
        bucket = participation_year[research_day.year]
        bucket["records"] += 1
        company = clean(row.get("id_empresa"))
        person = clean(row.get("id_cliente"))
        if company:
            bucket["companies"].add(company)
        if person:
            bucket["people"].add(person)

    six_fields = ["data_solicitacao", "data_divulgacao", "data_limite", "data_entrega", "participantes", "part_mercado"]
    completeness = [sum(bool(clean(row.get(field))) for row in researches) / len(researches) for field in six_fields]
    response_people = {clean(row.get("respondent_id")) for row in data["respostas"] if clean(row.get("respondent_id"))}
    consistency = [(number(row.get("participantes")), len(observed_companies.get(clean(row.get("id")), set()))) for row in researches]
    consistency = [(a, b) for a, b in consistency if a is not None and b]
    matching = sum(abs(a - b) < 0.001 for a, b in consistency)

    relations = {
        "respondentes → pesquisas": sum(clean(row.get("id_pesq")) in by_research for row in respondents),
        "questoes → pesquisas": sum(clean(row.get("pesquisa_id")) in by_research for row in data["questoes"]),
        "respostas → pesquisas": sum(clean(row.get("pesquisa_id")) in by_research for row in data["respostas"]),
    }
    hours = sum(bool(date(row.get("hora_inicio")) and date(row.get("hora_termino"))) for row in respondents)
    density = len(data["respostas"]) / len(response_people) if response_people else 0
    return {
        "researches": researches, "dated": dated, "years": years, "months": months,
        "weekdays": weekdays, "weekday_matches": weekday_matches, "weekday_total": len(valid_weekdays),
        "cycle_by_year": cycle_by_year, "cycle_all": cycle_all, "extension_by_year": extension_by_year,
        "participation_year": participation_year, "completeness": completeness, "completeness_fields": six_fields,
        "response_people": response_people, "density": density, "relations": relations,
        "hours": hours, "matching": matching, "consistency_total": len(consistency),
    }


def log_text(stats: dict[str, object], hashes: dict[str, str], files: dict[str, list[dict[str, str]]]) -> str:
    years: Counter[int] = stats["years"]  # type: ignore[assignment]
    months: Counter[int] = stats["months"]  # type: ignore[assignment]
    weekdays: Counter[str] = stats["weekdays"]  # type: ignore[assignment]
    cycle: list[float] = stats["cycle_all"]  # type: ignore[assignment]
    extensions: Counter[int] = stats["extension_by_year"]  # type: ignore[assignment]
    participation: dict[int, dict[str, object]] = stats["participation_year"]  # type: ignore[assignment]
    lines = [
        "# Análise quantitativa do snapshot", "", "Fonte: seis CSVs externos; dados brutos não versionados.",
        "Eixo temporal principal: data_divulgacao.", "",
        "[T1] Cobertura dos marcos", f"pesquisas: {len(files['pesquisas'])}",
        f"data_solicitacao: {sum(bool(date(r.get('data_solicitacao'))) for r in files['pesquisas'])} ({pct(sum(bool(date(r.get('data_solicitacao'))) for r in files['pesquisas']), len(files['pesquisas']))})",
        f"data_divulgacao: {len(stats['dated'])} ({pct(len(stats['dated']), len(files['pesquisas']))})",
        f"data_limite: {sum(bool(date(r.get('data_limite'))) for r in files['pesquisas'])} ({pct(sum(bool(date(r.get('data_limite'))) for r in files['pesquisas']), len(files['pesquisas']))})",
        f"data_entrega: {sum(bool(date(r.get('data_entrega'))) for r in files['pesquisas'])} ({pct(sum(bool(date(r.get('data_entrega'))) for r in files['pesquisas']), len(files['pesquisas']))})",
        f"prorrogada_ate: {sum(bool(date(r.get('prorrogada_ate'))) for r in files['pesquisas'])} ({pct(sum(bool(date(r.get('prorrogada_ate'))) for r in files['pesquisas']), len(files['pesquisas']))})",
        f"data_aprov: {sum(bool(date(r.get('data_aprov'))) for r in files['pesquisas'])} ({pct(sum(bool(date(r.get('data_aprov'))) for r in files['pesquisas']), len(files['pesquisas']))})", "",
        "[T2] Volume por ano de divulgação", *[f"{year}: {years[year]}" for year in sorted(years)],
        f"sem data: {len(files['pesquisas']) - len(stats['dated'])}", "", "[T4] Sazonalidade mensal",
        *[f"{month:02d}: {months[month]}" for month in range(1, 13)], "", "[T5] Dia da semana",
        *[f"código {key or 'sem código'}: {value}" for key, value in sorted(weekdays.items())],
        f"coerência contra data_divulgacao: {stats['weekday_matches']}/{stats['weekday_total']}", "",
        "[T6] Ciclo até a entrega", f"n: {len(cycle)}", f"mediana: {median(cycle):.1f}",
        f"média: {mean(cycle):.1f}", f"desvio-padrão: {stdev(cycle):.1f}",
        f"CV: {stdev(cycle) / mean(cycle) * 100:.1f}%", "",
        "[T7] Prorrogação", f"global: {sum(extensions.values())}/{len(files['pesquisas'])} ({pct(sum(extensions.values()), len(files['pesquisas']))})",
        *[f"{year}: {extensions[year]}" for year in sorted(extensions)], "", "[T8] Participação por ano",
    ]
    for year in sorted(participation):
        bucket = participation[year]
        lines.append(f"{year}: registros={bucket['records']}; empresas={len(bucket['companies'])}; pessoas={len(bucket['people'])}")
    lines += ["", "[4.5] Horários", f"registros com início e término: {stats['hours']}/{len(files['respondentes'])} ({pct(stats['hours'], len(files['respondentes']))})", "", "[QUALIDADE]", f"completude média dos seis campos: {mean(stats['completeness']) * 100:.1f}%", f"elementos por respondente: {stats['density']:.1f}"]
    lines += [f"{name}: {value}" for name, value in stats["relations"].items()]
    lines += [f"consistência participantes × observado: {stats['matching']}/{stats['consistency_total']}", "", "[HASHES SHA-256]"]
    lines += [f"{name}: {value}" for name, value in sorted(hashes.items())]
    lines += ["", "Nenhum CSV bruto foi adicionado ao Git; esta saída contém somente agregados."]
    return "\n".join(lines) + "\n"


def make_figures(stats: dict[str, object], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years: Counter[int] = stats["years"]  # type: ignore[assignment]
    months: Counter[int] = stats["months"]  # type: ignore[assignment]
    cycle: dict[int, list[float]] = stats["cycle_by_year"]  # type: ignore[assignment]
    participation: dict[int, dict[str, object]] = stats["participation_year"]  # type: ignore[assignment]
    completeness: list[float] = stats["completeness"]  # type: ignore[assignment]
    completeness_fields: list[str] = stats["completeness_fields"]  # type: ignore[assignment]
    output.mkdir(parents=True, exist_ok=True)

    plt.rcParams.update({
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "figure.dpi": 140,
        "font.size": 10,
    })

    def save(path: Path) -> None:
        plt.tight_layout()
        plt.savefig(path, bbox_inches="tight")
        plt.close()

    # fig1: série anual como linha baseada apenas em data_divulgacao.
    ordered_years = sorted(years)
    annual_values = [years[year] for year in ordered_years]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(ordered_years, annual_values, marker="o", linewidth=2.4, color="#2567AA")
    ax.fill_between(ordered_years, annual_values, color="#2567AA", alpha=0.12)
    for year, value in zip(ordered_years, annual_values):
        ax.annotate(str(value), (year, value), textcoords="offset points", xytext=(0, 8), ha="center")
    ax.set_title("Pesquisas divulgadas por ano")
    ax.set_ylabel("pesquisas")
    ax.set_xticks(ordered_years)
    ax.grid(axis="y", alpha=0.25)
    save(output / "fig1.png")

    # fig2: sazonalidade mensal como linha, evitando outra barra simples.
    monthly_values = [months[month] for month in range(1, 13)]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(MONTH_LABELS, monthly_values, marker="o", color="#E07E22", linewidth=2.2)
    ax.fill_between(range(len(MONTH_LABELS)), monthly_values, color="#E07E22", alpha=0.16)
    ax.set_title("Sazonalidade mensal das divulgações")
    ax.set_ylabel("pesquisas")
    ax.grid(axis="y", alpha=0.25)
    for idx, value in enumerate(monthly_values):
        ax.annotate(str(value), (idx, value), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    save(output / "fig2.png")

    # fig3: duração média e mediana do ciclo por ano, com taxa de prorrogação no eixo secundário.
    cycle_years = sorted(cycle)
    means = [mean(cycle[year]) for year in cycle_years]
    medians = [median(cycle[year]) for year in cycle_years]
    extension_by_year: Counter[int] = stats["extension_by_year"]  # type: ignore[assignment]
    extension_rates = [extension_by_year[year] * 100 / years[year] if years[year] else 0 for year in cycle_years]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(cycle_years, medians, marker="o", linewidth=2.2, color="#348455", label="mediana do ciclo")
    ax.plot(cycle_years, means, marker="s", linewidth=2.0, color="#7C53A0", label="média do ciclo")
    ax.set_title("Ciclo de entrega e prorrogação por ano")
    ax.set_ylabel("dias úteis")
    ax.set_xticks(cycle_years)
    ax.grid(axis="y", alpha=0.25)
    ax2 = ax.twinx()
    ax2.bar(cycle_years, extension_rates, color="#E0A800", alpha=0.28, label="taxa de prorrogação")
    ax2.set_ylabel("prorrogação (%)")
    lines, labels = ax.get_legend_handles_labels()
    bars, bar_labels = ax2.get_legend_handles_labels()
    ax.legend(lines + bars, labels + bar_labels, loc="upper right")
    save(output / "fig3.png")

    # fig4: participação por ano em barras agrupadas, separando registros, empresas e pessoas.
    participation_years = sorted(participation)
    records = [participation[year]["records"] for year in participation_years]
    companies = [len(participation[year]["companies"]) for year in participation_years]
    people = [len(participation[year]["people"]) for year in participation_years]
    positions = list(range(len(participation_years)))
    width = 0.24
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar([x - width for x in positions], records, width=width, color="#2567AA", label="registros")
    ax.bar(positions, people, width=width, color="#7C53A0", label="pessoas distintas")
    ax.bar([x + width for x in positions], companies, width=width, color="#348455", label="empresas distintas")
    ax.set_title("Participação observada por ano")
    ax.set_ylabel("contagem")
    ax.set_xticks(positions, participation_years)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=3, loc="upper left")
    save(output / "fig4.png")

    # fig5: completude horizontal por campo crítico, com linha de referência de 90%.
    completeness_pct = [value * 100 for value in completeness]
    ordered = sorted(zip(completeness_fields, completeness_pct), key=lambda item: item[1])
    labels = [field.replace("_", " ") for field, _ in ordered]
    values = [value for _, value in ordered]
    colors = ["#C94C4C" if value < 90 else "#348455" for value in values]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(labels, values, color=colors, alpha=0.9)
    ax.axvline(90, color="#444444", linestyle="--", linewidth=1.2, label="referência 90%")
    ax.set_title("Completude de campos críticos em pesquisas.csv")
    ax.set_xlabel("completude (%)")
    ax.set_xlim(0, 105)
    ax.grid(axis="x", alpha=0.2)
    for idx, value in enumerate(values):
        ax.text(min(value + 1, 101), idx, f"{value:.1f}%", va="center", fontsize=8)
    ax.legend(loc="lower right")
    save(output / "fig5.png")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados", type=Path, required=True, help="pasta somente leitura com os seis CSVs")
    parser.add_argument("--saida", type=Path, required=True, help="pasta de saída das cinco figuras")
    parser.add_argument("--log", type=Path, default=Path("docs/resultados_analise.txt"))
    args = parser.parse_args(argv)
    try:
        files, hashes = load_sources(args.dados)
        stats = calculate(files)
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(log_text(stats, hashes, files), encoding="utf-8")
        make_figures(stats, args.saida)
    except (OSError, ValueError, ZeroDivisionError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    print(f"OK: {sum(len(rows) for rows in files.values())} registros lidos; cinco figuras geradas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
