import uuid
from datetime import datetime
from decimal import Decimal

from fastapi_mongo_base.models import BusinessOwnedEntity
from pydantic import field_serializer, field_validator
from utils import numtools

from .config import PayPingConfig
from .schemas import PurchaseStatus


class Purchase(BusinessOwnedEntity):
    wallet_id: uuid.UUID
    amount: Decimal
    description: str
    callback_url: str

    phone: str | None = None

    is_test: bool = False
    status: PurchaseStatus = PurchaseStatus.INIT

    code: str | None = None

    failure_reason: str | None = None
    verified_at: datetime | None = None
    ref_id: int | None = None

    @field_validator("amount", mode="before")
    def validate_amount(cls, value):
        return numtools.decimal_amount(value)

    @field_serializer("status")
    def serialize_status(self, value):
        if isinstance(value, PurchaseStatus):
            return value.value
        if isinstance(value, str):
            return value
        return str(value)

    @classmethod
    async def get_purchase_by_code(cls, business_name: str, code: str):
        return await cls.find_one(
            cls.is_deleted == False,
            cls.business_name == business_name,
            cls.code == code,
        )

    async def success(self, ref_id: int):
        self.ref_id = ref_id
        self.status = "SUCCESS"
        self.verified_at = datetime.now()
        await self.save()

    async def fail(self, failure_reason: str = None):
        self.status = "FAILED"
        self.failure_reason = failure_reason
        await self.save()

    @property
    def config(self):
        return PayPingConfig()

    @property
    def is_successful(self):
        return self.status == "SUCCESS"

    @property
    def start_payment_url(self):
        return self.config.payment_request_url(self.code)
