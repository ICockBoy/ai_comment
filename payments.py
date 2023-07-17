import asyncio
from datetime import datetime

from glQiwiApi import QiwiP2PClient

from config import *
from db_manage import *


class Payments:

    def __init__(self):

        self.qiwi_secret_p2p_token = QIWI_TOKEN_P2P_SECRET
        self.proxy_step = "http://referrerproxy-env.eba-cxcmwwm7.us-east-1.elasticbeanstalk.com/proxy/p2p/"

        self.bills = {}

    async def create_payment(self, amount: float, user_id: int) -> dict:

        async with QiwiP2PClient(secret_p2p=self.qiwi_secret_p2p_token, shim_server_url=self.proxy_step) as p2p:
            bill = await p2p.create_p2p_bill(amount=amount, pay_source_filter=["card", "qw", "mobile"])

        self.bills[bill.id] = {
            "bill_object": bill,
            "amount": amount,
            "user_id": user_id
        }

        return {"url": bill.pay_url, "bill_id": bill.id, "amount": bill.amount}
    

    async def check_payment(self, bill_id: str) -> bool:

        async with QiwiP2PClient(secret_p2p=self.qiwi_secret_p2p_token, shim_server_url=self.proxy_step) as p2p:
            
            if not bill_id in self.bills.keys():
                return

            bill_data = self.bills[bill_id]

            status_payment = await p2p.check_if_bill_was_paid(bill_data["bill_object"])
            # status_payment = True

            if not status_payment:
                return False
            
            update_user_balance(
                user_id=bill_data["user_id"],
                value=bill_data["amount"]
            )

            del self.bills[bill_id]

            return bill_data["amount"]