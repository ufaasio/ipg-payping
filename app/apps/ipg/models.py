from datetime import datetime

from fastapi_mongo_base.models import BusinessOwnedEntity
from pydantic import field_serializer, field_validator
from utils import numtools

from .config import PayPingConfig
from .schemas import PurchaseSchema, PurchaseStatus


class Purchase(PurchaseSchema, BusinessOwnedEntity):
    callback_url: str

    class Settings:
        indexes = BusinessOwnedEntity.Settings.indexes

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
        await self.save_report(f'purchase successfully verified with ref_id "{ref_id}"')
        # await self.save()

    async def fail(self, failure_reason: str = None):
        self.status = "FAILED"
        self.failure_reason = failure_reason
        await self.save_report(f'purchase failed because of "{failure_reason}"')
        # await self.save()

    @property
    def config(self):
        return PayPingConfig()

    @property
    def is_successful(self):
        return self.status == "SUCCESS"

    @property
    def start_payment_url(self):
        return self.config.payment_request_url(self.code)
