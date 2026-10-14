from pydantic import BaseModel, ConfigDict, Field


class BarcodeRequest(BaseModel):
    barcode: str = Field(
        min_length=1,
        max_length=2000,
        description="Text read by the camera: DANFE barcode or NFC-e QR code URL.",
        examples=["35240112345678000190550010000123451000000013"],
    )


class AccessKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(description="Full access key (44 digits).")
    state_code: str = Field(description="IBGE state code of the issuer.")
    year_month: str = Field(description="Issue year and month (YYMM).")
    cnpj: str = Field(description="Issuer CNPJ.")
    model: str = Field(description="55 = NF-e, 65 = NFC-e.")
    series: str
    number: str = Field(description="Invoice number with leading zeros.")
    invoice_number: int = Field(description="Invoice number without leading zeros.")
    emission_type: str
    numeric_code: str
    check_digit: str
