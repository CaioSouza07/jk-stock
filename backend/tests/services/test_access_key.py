import pytest

from app.services.access_key import (
    InvalidAccessKey,
    calculate_check_digit,
    extract_key,
    read_access_key,
)
from tests.conftest import ACCESS_KEY


def test_valid_check_digit():
    assert calculate_check_digit(ACCESS_KEY[:43]) == 3


def test_parse_key():
    k = read_access_key(ACCESS_KEY)
    assert k.state_code == "35"
    assert k.year_month == "2401"
    assert k.cnpj == "12345678000190"
    assert k.model == "55"
    assert k.series == "001"
    assert k.number == "000012345"
    assert k.invoice_number == 12345
    assert k.emission_type == "1"
    assert k.numeric_code == "00000001"
    assert k.check_digit == "3"


def test_key_with_spaces():
    formatted = " ".join(ACCESS_KEY[i : i + 4] for i in range(0, 44, 4))
    assert read_access_key(formatted).key == ACCESS_KEY


def test_key_inside_nfce_qr_url():
    url = f"https://www.nfce.fazenda.sp.gov.br/qrcode?p={ACCESS_KEY}|2|1|1|ABCDEF"
    assert extract_key(url) == ACCESS_KEY


def test_more_than_44_digits_does_not_match():
    assert extract_key(ACCESS_KEY + "9") is None


def test_key_not_found():
    with pytest.raises(InvalidAccessKey, match="não encontrada"):
        read_access_key("123")


def test_wrong_check_digit():
    with pytest.raises(InvalidAccessKey, match="dígito verificador"):
        read_access_key(ACCESS_KEY[:43] + "4")


def test_remainder_below_2_gives_zero():
    # total 0 -> remainder 0; "0"*42 + "5" -> total 10 -> remainder 10 -> digit 1
    assert calculate_check_digit("0" * 43) == 0
    assert calculate_check_digit("0" * 42 + "5") == 1
