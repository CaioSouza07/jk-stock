"""Extraction and validation of the NF-e / NFC-e access key (44 digits)."""

import re
from dataclasses import dataclass

from app.core.exceptions import AppError

ACCESS_KEY_RE = re.compile(r"(?<!\d)\d{44}(?!\d)")


class InvalidAccessKey(AppError):
    message = "Chave de acesso inválida."


@dataclass(frozen=True)
class AccessKey:
    key: str
    state_code: str
    year_month: str
    cnpj: str
    model: str
    series: str
    number: str
    emission_type: str
    numeric_code: str
    check_digit: str

    @property
    def invoice_number(self) -> int:
        """Invoice number without leading zeros (used to search Olist)."""
        return int(self.number)


def calculate_check_digit(base43: str) -> int:
    """Modulo 11 with weights 2..9 applied from right to left."""
    total = sum(int(d) * (2 + i % 8) for i, d in enumerate(reversed(base43)))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def extract_key(text: str) -> str | None:
    """Find the key in a scanned code (DANFE barcode or NFC-e QR code URL)."""
    no_spaces = re.sub(r"\s+", "", text or "")
    m = ACCESS_KEY_RE.search(no_spaces)
    return m.group(0) if m else None


def parse_key(key: str) -> AccessKey:
    return AccessKey(
        key=key,
        state_code=key[0:2],
        year_month=key[2:6],
        cnpj=key[6:20],
        model=key[20:22],
        series=key[22:25],
        number=key[25:34],
        emission_type=key[34],
        numeric_code=key[35:43],
        check_digit=key[43],
    )


def read_access_key(text: str) -> AccessKey:
    """Extract, validate the check digit and parse the key. Raises InvalidAccessKey."""
    key = extract_key(text)
    if key is None:
        raise InvalidAccessKey("Chave de acesso não encontrada no código lido.")
    if calculate_check_digit(key[:43]) != int(key[43]):
        raise InvalidAccessKey("Chave de acesso inválida (dígito verificador não confere).")
    return parse_key(key)
