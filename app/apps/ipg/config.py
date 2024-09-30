class PayPingConfig:
    def __init__(self):
        self.base_url = "https://api.payping.ir/v2/pay"

    def payment_request_url(self, code) -> str:
        return f"{self.base_url}/gotoipg/{code}"

    @property
    def payment_verify_url(self) -> str:
        return f"{self.base_url}/verify"

    @property
    def start_payment_url(self) -> str:
        return f"{self.base_url}"
