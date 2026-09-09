"""Conversões estritas: erro estável e sem valor de negócio na mensagem."""

import re
import unicodedata
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo


class ConversionError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def text(value):
    if not isinstance(value, str):
        raise ConversionError("INVALID_TEXT")
    return unicodedata.normalize("NFC", value).strip()


def number(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ConversionError("INVALID_NUMBER")
    rendered = str(value).strip()
    if not re.fullmatch(r"[+-]?(?:[0-9]+(?:[.,][0-9]+)?|[0-9]{1,3}(?:\.[0-9]{3})+,[0-9]+)", rendered):
        raise ConversionError("INVALID_NUMBER")
    if "," in rendered:
        rendered = rendered.replace(".", "").replace(",", ".")
    try:
        result = Decimal(rendered)
    except InvalidOperation:
        raise ConversionError("INVALID_NUMBER") from None
    if not result.is_finite():
        raise ConversionError("INVALID_NUMBER")
    return result


def identifier(value):
    # Reject floats even when integral: precision may already have been lost.
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ConversionError("INVALID_ID")
    rendered = str(value).strip()
    if not re.fullmatch(r"[0-9]+(?:\.0+)?", rendered) or len(rendered) > 128:
        raise ConversionError("INVALID_ID")
    return str(int(rendered.split(".")[0]))


def integer(value):
    result = number(value)
    if result != result.to_integral_value() or not -(2**63) <= result < 2**63:
        raise ConversionError("INVALID_INTEGER")
    return int(result)


def decimal(value, percent=False):
    if percent and isinstance(value, str):
        value = value.strip()
        if value.endswith("%"):
            value = value[:-1].strip()
    result = number(value)
    if abs(result) >= Decimal("1000000000000") or result.as_tuple().exponent < -6:
        raise ConversionError("DECIMAL_PRECISION")
    if percent and not Decimal(0) <= result <= Decimal(100):
        raise ConversionError("PERCENT_RANGE")
    return result


def civil_date(value):
    if isinstance(value, datetime):
        raise ConversionError("INVALID_DATE")
    if isinstance(value, date):
        parsed = value
    else:
        if not isinstance(value, str):
            raise ConversionError("INVALID_DATE")
        parsed = None
        for pattern in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                candidate = datetime.strptime(value.strip(), pattern)
                parsed = candidate.date()
                break
            except ValueError:
                pass
        if parsed is None:
            raise ConversionError("INVALID_DATE")
    if not 1900 <= parsed.year <= 2299:
        raise ConversionError("DATE_RANGE")
    return parsed


def instant(value, source_timezone=None):
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        rendered = value.strip()
        parsed = None
        if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2}(?:\.[0-9]{1,6})?)?(?:Z|[+-][0-9]{2}:[0-9]{2})?", rendered):
            try:
                parsed = datetime.fromisoformat(rendered.replace("Z", "+00:00"))
            except ValueError:
                pass
        if parsed is None:
            for pattern in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
                try:
                    parsed = datetime.strptime(rendered, pattern)
                    break
                except ValueError:
                    pass
        if parsed is None:
            raise ConversionError("INVALID_DATETIME")
    else:
        raise ConversionError("INVALID_DATETIME")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        if not source_timezone:
            raise ConversionError("TIMEZONE_REQUIRED")
        zone = ZoneInfo(source_timezone)
        variants = {parsed.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
                    for fold in (0, 1)
                    if parsed.replace(tzinfo=zone, fold=fold).astimezone(timezone.utc)
                    .astimezone(zone).replace(tzinfo=None) == parsed}
        if len(variants) != 1:
            raise ConversionError("AMBIGUOUS_OR_NONEXISTENT_TIME")
        parsed = variants.pop()
    parsed = parsed.astimezone(timezone.utc)
    if not 1900 <= parsed.year <= 2299:
        raise ConversionError("DATE_RANGE")
    return parsed


def boolean(value):
    if isinstance(value, bool):
        return value
    canonical = text(value).casefold()
    values = {"sim": True, "true": True, "não": False, "nao": False, "false": False}
    if canonical not in values:
        raise ConversionError("INVALID_BOOLEAN")
    return values[canonical]
