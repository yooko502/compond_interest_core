import math
from dataclasses import dataclass
from typing import Literal
import pandas as pd


@dataclass
class WithdrawalResult:
    """Withdrawal result dataclass"""
    years: float | int | tuple  # 用于返回可以持续的年数, tuple用于分别返回年数和月数
    monthly_withdrawal: float | int  # 用于返回每月提取的金额
    initial_balance: float | int  # 用于返回所需的初始金额
    monthly_balances: pd.DataFrame  # 用于返回每月的资产变化
    no_invest: float | int | tuple  # 用于各个方法之间，不投资的情况下的返回值，tuple用于分别返回年数和月数


class WithdrawalSimulation:
    """
    A class to simulate withdrawals from an investment account.
    本身属性只需要传入预期年化收益率

    Parameters:
        annual_return (float): Expected annual return rate (as decimal, e.g., 0.1 for 10%)
    """

    def __init__(self, annual_return: float):
        self.annual_return = annual_return
        self.monthly_return_rate = self._calculate_monthly_return()

    def _calculate_monthly_return(self) -> float:
        """Calculate the monthly return from the annual return. 使用的是几何平均数来计算月收益率"""
        return pow(1 + self.annual_return, 1 / 12) - 1

    def simulate_years(self,
                       initial_balance: float,
                       monthly_withdrawal: float) -> WithdrawalResult:
        """
        Simulate how many years the investment will last given an initial balance and monthly withdrawal amount.
        根据已有资产数额和每月提取金额，计算可以持续的年数。
        Parameters:
            initial_balance (float): Initial investment balance
            monthly_withdrawal (float): Monthly withdrawal amount

        Returns:
            WithdrawalResult: Result including number of years and monthly balances
        """
        if initial_balance <= 0 or monthly_withdrawal <= 0:
            raise ValueError("Initial balance and monthly withdrawal must be greater than 0.")
        balance = initial_balance  # 初始的资产金额
        months = 0  # 用于记录持续的月数
        monthly_balances = []  # 用于记录每月的资产变化

        while balance - monthly_withdrawal > 0:  # 当资产金额大于每月取现金额时，继续循环，来记录资产变化以及持续的月数
            balance = balance * (1 + self.monthly_return_rate) - monthly_withdrawal
            monthly_balances.append(balance)
            months += 1

        monthly_balances_df = pd.DataFrame(monthly_balances, columns=['Balance'])
        monthly_balances_df.index.name = 'Month'

        no_invest = initial_balance / monthly_withdrawal  # 这个方法中计算的不投资的情况下可以持续的月数
        no_invest_year = int(no_invest // 12)  # 获取年数
        no_invest_month = int(no_invest % 12)  # 获取月数

        return WithdrawalResult(years=(int(months // 12), int(months % 12)), monthly_withdrawal=monthly_withdrawal,
                                initial_balance=initial_balance, monthly_balances=monthly_balances_df,
                                no_invest=(no_invest_year, no_invest_month))  # 返回值中全部返回了可以持续的年数以及月数

    def simulate_monthly_withdrawal(self,
                                    initial_balance: float,
                                    years: float) -> WithdrawalResult:
        """
        Simulate the monthly withdrawal amount given an initial balance and the number of years to withdraw.
        用来计算在已知的资产金额和持续的年数下，每月可以提取的金额。

        Parameters:
            initial_balance (float): Initial investment balance
            years (float): Number of years to withdraw

        Returns:
            WithdrawalResult: Result including monthly withdrawal amount and monthly balances
        """
        if initial_balance <= 0 or years <= 0:
            raise ValueError("Initial balance and years must be greater than 0.")
        months = int(years * 12)  # 将年数转换为月数
        balance = initial_balance
        monthly_balances = []

        if self.monthly_return_rate == 0:
            monthly_withdrawal = balance / months
            for _ in range(months):
                balance -= monthly_withdrawal
                monthly_balances.append(balance)
            monthly_balances_df = pd.DataFrame(monthly_balances, columns=['Balance'])
            monthly_balances_df.index.name = 'Month'
            return WithdrawalResult(years=years, monthly_withdrawal=monthly_withdrawal, initial_balance=initial_balance,
                                    monthly_balances=monthly_balances_df)

        numerator = balance * self.monthly_return_rate
        denominator = (1 - pow(1 + self.monthly_return_rate, -months))
        monthly_withdrawal = numerator / denominator

        for _ in range(months):
            if balance - monthly_withdrawal < 0:  # 当余额小于取现额的时候，停止循环
                break
            balance = balance * (1 + self.monthly_return_rate) - monthly_withdrawal
            monthly_balances.append(balance)

        monthly_balances_df = pd.DataFrame(monthly_balances, columns=['Balance'])
        monthly_balances_df.index.name = 'Month'

        no_invest = initial_balance / months

        return WithdrawalResult(years=years, monthly_withdrawal=monthly_withdrawal, initial_balance=initial_balance,
                                monthly_balances=monthly_balances_df, no_invest=no_invest)

    def simulate_initial_balance(self,
                                 monthly_withdrawal: float,
                                 years: float) -> WithdrawalResult:
        """
        Simulate the required initial balance given a monthly withdrawal amount and the number of years to withdraw.

        Parameters:
            monthly_withdrawal (float): Monthly withdrawal amount
            years (float): Number of years to withdraw

        Returns:
            WithdrawalResult: Result including required initial balance and monthly balances
        """
        if monthly_withdrawal <= 0 or years <= 0:
            raise ValueError("Monthly withdrawal and years must be greater than 0.")
        months = int(years * 12)
        balance = 0
        monthly_balances = []

        if self.monthly_return_rate == 0:
            initial_balance = monthly_withdrawal * months
            for _ in range(months):
                balance -= monthly_withdrawal
                monthly_balances.append(balance)
            monthly_balances_df = pd.DataFrame(monthly_balances, columns=['Balance'])
            monthly_balances_df.index.name = 'Month'
            return WithdrawalResult(years=years, monthly_withdrawal=monthly_withdrawal, initial_balance=initial_balance,
                                    monthly_balances=monthly_balances_df)

        numerator = monthly_withdrawal * (1 - pow(1 + self.monthly_return_rate, -months))
        denominator = self.monthly_return_rate
        initial_balance = numerator / denominator
        balance = initial_balance

        for _ in range(months):
            balance = balance * (1 + self.monthly_return_rate) - monthly_withdrawal
            monthly_balances.append(balance)

        monthly_balances_df = pd.DataFrame(monthly_balances, columns=['Balance'])
        monthly_balances_df.index.name = 'Month'

        no_invest = months * monthly_withdrawal  # 这个方法中计算的不投资的情况下所需的初始金额

        return WithdrawalResult(years=years, monthly_withdrawal=monthly_withdrawal, initial_balance=initial_balance,
                                monthly_balances=monthly_balances_df, no_invest=no_invest)


# Example usage
if __name__ == "__main__":
    simulation = WithdrawalSimulation(annual_return=0.1)

    # Example 1: Calculate how many years the investment will last
    result = simulation.simulate_years(initial_balance=100000, monthly_withdrawal=1000)
    print(f"Years the investment will last: {result.years[0]} years and {result.years[1]} months")
    print(result.monthly_balances)
    print(f"\n No invest: {result.no_invest[0]} years and {result.no_invest[1]} months")

    # Example 2: Calculate the monthly withdrawal amount
    result = simulation.simulate_monthly_withdrawal(initial_balance=100000, years=20)
    print(f"Monthly withdrawal amount: {result.monthly_withdrawal:.2f}")
    print(result.monthly_balances)
    print(f"\n No invest: {result.no_invest:.2f}")

    # Example 3: Calculate the required initial balance
    result = simulation.simulate_initial_balance(monthly_withdrawal=1000, years=20)
    print(f"Required initial balance: {result.initial_balance:.2f}")
    print(result.monthly_balances)
    print(f"\n No invest: {result.no_invest:.2f}")
