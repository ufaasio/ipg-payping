from core import exceptions


class PayPingException(exceptions.BaseHTTPException):
    """
    BaseClass for exceptions
    """

    def __init__(self, message: str = None):
        super().__init__(400, "payping_exception", message)


class PurchaseDoesNotExist(PayPingException):
    """No purchase submitted with this code"""

    def __init__(self, code: str):
        super().__init__(f"No purchase submitted with this code: {code}")


class PurchaseDataIsNotValid(PayPingException):
    """The data was not valid for PayPing gateway"""

    def __init__(self, data: str):
        super().__init__(f"The data was not valid for PayPing gateway: {data}")


class CouldNotStartPurchase(PayPingException):
    """did not get start code from PayPing"""

    def __init__(self, response: str):
        super().__init__(f"did not get start code from PayPing: {response}")


class AmountIsLessThanMinimum(PayPingException):
    """minimum amount to start purchase is 1000"""

    def __init__(self, amount: int):
        super().__init__(f"minimum amount to start purchase is 1000: {amount}")


class CallBackUrlNotSet(PayPingException):
    """Specify ZARINPAL_CALLBACK_URL in settings"""

    def __init__(self, callback_url: str):
        super().__init__(f"Specify ZARINPAL_CALLBACK_URL in settings: {callback_url}")


class MerchantIdNotSet(PayPingException):
    """Specify ZARINPAL_MERCHANT_ID in settings"""

    def __init__(self, merchant_id: str):
        super().__init__(f"Specify ZARINPAL_MERCHANT_ID in settings: {merchant_id}")
