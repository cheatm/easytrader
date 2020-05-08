from decimal import Decimal
import easytrader.exceptions
from datetime import datetime


class DummyTrader(object):

    def __init__(self):
        self.closed_entrusts = {}
        self.pending_entrusts = {}
        self.positions = {}
        self._entrust_no = 0

    def connect(self, path: str):
        pass

    def enable_type_keys_for_editor(self):
        pass

    def next_entrust_no(self):
        self._entrust_no += 1
        return self._entrust_no

    @property
    def app(self):
        """Return current app instance"""
        pass

    @property
    def main(self):
        """Return current main window instance"""
        pass

    @property
    def config(self):
        """Return current config instance"""
        pass

    def wait(self, seconds: float):
        """Wait for operation return"""
        pass

    def refresh(self):
        """Refresh data"""
        pass

    def is_exist_pop_dialog(self):
        pass
    
    @staticmethod
    def entrust_result(entrust: dict):
        result = entrust.copy()
        for name in ("委托价格", "成交均价"):
            result[name] = float(result[name])
        return result
    
    @staticmethod
    def position_result(position: dict):
        result = position.copy()
        for name in ("成本价", "市价", "盈亏"):
            result[name] = float(result[name])
        return result

    @property
    def today_entrusts(self):
        self.maker_all()
        return [self.entrust_result(entrust) for entrust in self.closed_entrusts.values()]

    @property
    def position(self):
        return [self.position_result(position) for position in self.positions.values()]

    def maker_all(self):
        while self.pending_entrusts:
            en, entrust = self.pending_entrusts.popitem()
            entrust["成交数量"] = entrust["委托数量"]
            entrust["成交均价"] = entrust["委托价格"]
            entrust["备注"] = "已成"
            self.closed_entrusts[en] = entrust
            if entrust["证券代码"] not in self.positions:
                self.positions[entrust["证券代码"]] = {
                    "证券代码": entrust["证券代码"],
                    "证券名称": entrust["证券名称"],
                    "股票余额": 0,
                    "实际数量": 0,
                    "可用余额": 0,
                    "冻结数量": 0,
                    "成本价": Decimal(0),
                    "市价": Decimal(0),
                    "盈亏": Decimal(0),
                    "盈亏比(%)": 0,
                    "当日盈亏": 0,
                    "当日盈亏比(%)": 0,
                    "市值": 0,
                    "仓位占比(%)": 0,
                    "交易市场": entrust["交易市场"],
                    "明细": ""
                }
            position = self.positions[entrust["证券代码"]]
            
            if entrust["操作"] == "买入":
                position["成本价"] = (position["成本价"] * position["实际数量"] + entrust["成交数量"] * entrust["成交均价"]) / (position["实际数量"] + entrust["成交数量"])
                position["股票余额"] += entrust["成交数量"]
                position["实际数量"] += entrust["成交数量"]
                position["可用余额"] += entrust["成交数量"]
                position["市价"] = entrust["成交均价"]
            else:
                remain_amount = position["实际数量"] - entrust["成交数量"]
                if remain_amount > 0:
                    position["成本价"] = (position["成本价"] * position["实际数量"] - entrust["成交数量"] * entrust["成交均价"]) / remain_amount
                else:
                    position["成本价"] = Decimal(0)
                position["股票余额"] -= entrust["成交数量"]
                position["实际数量"] -= entrust["成交数量"]
                position["可用余额"] -= entrust["成交数量"]
                position["市价"] = entrust["成交均价"]
                

    def buy(self, security, price, amount, **kwargs):
        time = kwargs["requested_time"]
        entrust_no = self.next_entrust_no()
        market = "深Ａ" if int(security) < 600000 else "沪Ａ"
        entrust = {
            "委托时间": datetime.fromtimestamp(time).strftime("%H:%M:%S"),
            "证券代码": security,
            "证券名称": "",
            "操作": "买入",
            "备注": "已报",
            "委托数量": int(amount),
            "成交数量": 0,
            "委托价格": Decimal(price),
            "成交均价": 0,
            "撤消数量": 0,
            "合同编号": entrust_no,
            "交易市场": market,
            "股东账户": 0,
        }
        self.pending_entrusts[entrust_no] = entrust

        return {"entrust_no": entrust_no}

    def sell(self, security, price, amount, **kwargs): 
        if security not in self.positions:
            raise easytrader.exceptions.TradeError(f"{security} available balance not enough: 0")
        position = self.positions[security]
        if position["可用余额"] < int(amount):
            raise easytrader.exceptions.TradeError(f"{security} available balance not enough: {position['可用余额']}")
        time = kwargs["requested_time"]
        entrust_no = self.next_entrust_no()
        market = "深Ａ" if int(security) < 600000 else "沪Ａ"
        entrust = {
            "委托时间": datetime.fromtimestamp(time).strftime("%H:%M:%S"),
            "证券代码": security,
            "证券名称": "",
            "操作": "卖出",
            "备注": "已报",
            "委托数量": int(amount),
            "成交数量": 0,
            "委托价格": Decimal(price),
            "成交均价": 0,
            "撤消数量": 0,
            "合同编号": entrust_no,
            "交易市场": market,
            "股东帐户": 0,
        }
        self.pending_entrusts[entrust_no] = entrust
        return {"entrust_no": entrust_no}

    def cancel_entrust(self, entrust_no): 
        if entrust_no in self.pending_entrusts:
            entrust = self.pending_entrusts.pop(entrust_no)
            entrust["备注"] = "已撤"
            entrust["撤消数量"] = entrust["委托数量"] - entrust["成交数量"]
            self.closed_entrusts[entrust_no] = entrust
        return {"message": ""}
