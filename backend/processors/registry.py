from typing import Optional

from .payflow import payflow_instance
from .stripeconnect import stripeconnect_instance
from .latampay import latampay_instance
from .base import BaseProcessor

PROCESSORS = {
    "PayFlow": payflow_instance,
    "StripeConnect": stripeconnect_instance,
    "LatamPay": latampay_instance,
}


def get_processor(name: str) -> Optional[BaseProcessor]:
    return PROCESSORS.get(name)
