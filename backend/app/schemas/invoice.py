from pydantic import BaseModel, ConfigDict, Field


class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int | None
    code: str = Field(description="Product SKU.")
    description: str
    unit: str
    quantity: float
    unit_price: float
    total_price: float
    image_url: str | None = Field(description="First product image, if any.")
    images: list[str]


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Invoice id in Olist.")
    number: str
    series: str
    access_key: str
    issued_at: str | None
    customer_name: str | None
    total: float
    items: list[InvoiceItemResponse]
