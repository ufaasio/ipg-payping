import logging

from apps.config.models import Configuration
from fastapi_mongo_base.utils import aionetwork
from server.config import Settings
from ufaas_fastapi_business.models import Business

from .exceptions import PayPingException, PurchaseDoesNotExist
from .models import Purchase
from .schemas import ProposalCreateSchema


async def start_purchase(business: Business, purchase: Purchase) -> dict:
    callback_url = (
        f"https://{business.domain}{Settings.base_path}/purchases/{purchase.uid}/verify"
    )
    # TODO: fix this.
    # I have to change it because of pixy.ir do not have token
    if business.name == "pixy":
        callback_url = f"https://wallet.pixiee.io{Settings.base_path}/purchases/{purchase.uid}/verify"

    config: Configuration = await Configuration.get_config(business.name)

    # data = {
    #     "MerchantID": business.secret.merchant_id,
    #     "Amount": int(purchase.amount),
    #     "Description": purchase.description,
    #     "Mobile": purchase.phone,
    #     "CallbackURL": callback_url,
    # }

    # all units in Payping are in Toman
    data = {
        "amount": int(purchase.amount // 10),
        "description": purchase.description,
        "returnUrl": callback_url,
        "clientRefId": str(purchase.uid),
        "payerIdentity": purchase.phone,
    }
    headers = {"Authorization": f"Bearer {config.merchant_id}"}

    response = await aionetwork.aio_request(
        method="post",
        url=purchase.config.start_payment_url,
        json=data,
        headers=headers,
        timeout=10,
    )

    logging.info(f"{response=}")

    purchase.code = response.get("code")
    purchase.status = "PENDING"
    await purchase.save()
    return {
        "status": True,
        "code": purchase.code,
        "url": purchase.config.payment_request_url(purchase.code),
    }


async def verify_purchase(
    business: Business, item: Purchase, code: str, refid: str, **kwargs
) -> Purchase:
    purchase: Purchase = await Purchase.get_purchase_by_code(business.name, code)
    if not purchase:
        raise PurchaseDoesNotExist(code)

    if purchase.uid != item.uid:
        raise PayPingException(f"uid does not match for {code}")

    if purchase.status in ["SUCCESS", "FAILED"]:
        return purchase

    config: Configuration = await Configuration.get_config(business.name)

    headers = {"Authorization": f"Bearer {config.merchant_id}"}

    data = {"amount": int(purchase.amount // 10), "refId": refid}
    purchase.meta_data = (purchase.meta_data or {}) | kwargs

    try:
        response = await aionetwork.aio_request(
            method="post",
            url=purchase.config.payment_verify_url,
            json=data,
            headers=headers,
        )
        logging.info(f"response: {response}")
        await purchase.success(refid)
    except Exception as e:
        logging.error(f"Error in verify_purchase {type(e)} {e}")
        await purchase.fail(refid)

    return purchase


async def create_proposal(purchase: Purchase, business: Business) -> dict:
    config: Configuration = await Configuration.get_config(business.name)

    proposal_data = ProposalCreateSchema(
        amount=purchase.amount,
        description=purchase.description,
        currency=Settings.currency,
        task_status="init",
        participants=[
            {"wallet_id": purchase.wallet_id, "amount": purchase.amount},
            {"wallet_id": config.income_wallet_id, "amount": -purchase.amount},
        ],
        note=None,
        meta_data=None,
    ).model_dump_json()

    access_token = await business.get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "content-type": "application/json",
    }

    response = await aionetwork.aio_request(
        method="post",
        url=f"{business.config.core_url}api/v1/proposals/",
        data=proposal_data,
        headers=headers,
        raise_exception=False,
    )
    if "error" in response:
        logging.error(f"Error in create_proposal {response}")
        raise PayPingException(f"Error in create_proposal {response}")
    return response
