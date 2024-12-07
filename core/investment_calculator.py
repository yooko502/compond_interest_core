from numpy import zeros, array, ndarray
from numpy import round as np_round
from dataclasses import dataclass
from pandas import date_range, DataFrame, Timestamp
import math
from typing import Literal, Dict, Optional
from matplotlib import pyplot as plt


@dataclass
class InvestmentResult:
    """investment result dataclass"""
    final_balance: float | int
    total_principal: float | int
    total_return: float | int
    monthly_data: DataFrame


def _validate_inputs(params: Dict) -> None:
    """Validate input parameters."""
    if params['y_return'] < 0:
        raise ValueError("Yearly return rate cannot be less than 0")
    if params['horizon'] <= 0:
        raise ValueError("Investment horizon must be positive")
    if params['m_investment'] < 0:
        raise ValueError("Monthly investment cannot be negative")
    if params['init_balance'] < 0:
        raise ValueError("Initial balance cannot be negative")
    if params['method'] not in ["geometric", "arithmetic"]:
        raise ValueError("Method must be either 'geometric' or 'arithmetic'")
    if not isinstance(params['increment'], (int, float)):
        raise ValueError("Increment amount must be a number")
    if params['incre_period'] < 0:
        raise ValueError("Increment period cannot be negative")


class InvestmentCalculator:
    """
    A class to calculate the investment return and investment plan.

     Parameters:
        y_return (float): Yearly return rate (as decimal, e.g., 0.1 for 10%)
        horizon (int): Investment horizon in years
        m_investment (float): Monthly investment amount
        init_balance (float): Initial balance (default: 0)
        method (str): Method to calculate monthly return - "geometric" or "arithmetic" (default: "geometric")
        increment (float): Annual increment to monthly investment. Defaults to 0.
        incre_period (int): Number of years to apply increment. Defaults to 0.
    """

    def __init__(self, y_return: float = 0,
                 horizon: int = 1,
                 m_investment: float = 0,
                 init_balance: float = 0,
                 method: Literal["geometric", "arithmetic"] = "geometric",
                 increment: float = 0,
                 incre_period: int = 0):

        # Input validation
        _validate_inputs(locals())

        # Protected attributes in this class (suggest to use in subclasses and this class)
        self._y_return = y_return
        self._horizon = horizon
        self._m_investment = m_investment
        self._init_balance = init_balance
        self._method = method
        self._increment = increment
        self._increment_period = incre_period

        # Protected attributes to be used in this class only
        self.__monthly_return = self._calculate_monthly_return()

    @property
    def y_return(self) -> float:
        """yearly return rate"""
        return self._y_return

    @property
    def horizon(self) -> int:
        """investment horizon in years"""
        return self._horizon

    @property
    def m_investment(self) -> float:
        """monthly investment amount"""
        return self._m_investment

    @property
    def init_balance(self) -> float:
        """initial balance"""
        return self._init_balance

    def _calculate_monthly_return(self) -> float:
        """Calculate the monthly return of an expected yearly return."""
        if self._method == "geometric":
            return pow(1 + self.y_return, 1 / 12) - 1
        elif self._method == "arithmetic":
            return self.y_return / 12

    def automatic_investment(self,
                             horizon: float = None,
                             m_investment: float = None,
                             monthly_rate: float = None) -> InvestmentResult:
        """
        Calculate the final balance with optional periodic investment increment.

        假设在每个月的月初进行定投，每月定投额为m_investment，年收益率为y_return，投资期为horizon年。
        因此，每个月月初的余额计算公式为：balance = balance * (1 + monthly_return) + m_investment
        这里，balance为上个月月初的余额，这一部分会享受一整个月的收益。

        是否增加定投额的判断
        1.是否经过了一年：(i+1) % 12 == 0
        2.增加定投额是否为0：increment != 0
        3.当前年限是否在增加定投额年限内：year_num <= incre_period
        4.判断是否为第一年，第一年不进行增加定投额的操作，增加定投额从第二年开始：year_num != 0

        Parameters:三个可选参数主要用于使用back_to_present方法计算完所需的值后，再次调用automatic_investment方法
            1.horizon (float): Investment horizon in years (default: None, use class attribute)
            2.m_investment (float): Monthly investment amount (default: None, use class attribute)
            3.monthly_rate (float): Monthly return rate (default: None, use class attribute)
            :return: InvestmentResult
        Returns:
            float: Final balance after investment horizon.
        """

        """计算投资期数以及设置当前月投资额和期望收益率"""
        month_num = self.horizon * 12 if horizon is None else horizon * 12
        current_monthly_investment = self.m_investment if m_investment is None else m_investment
        excepted_return = self.__monthly_return if monthly_rate is None else monthly_rate

        """initial data array"""
        """第一个元素为初始值，后续元素开始依次为投资一个月，两个月，三个月……时的月初时候的数值"""
        balances = zeros(month_num + 1)  # 账户余额
        principals = zeros(month_num + 1)  # 投入本金
        returns = zeros(month_num + 1)  # 投资收益
        investment_amount = zeros(month_num + 1)  # 投资额

        """setting initial value"""
        """初始余额设置为0的情况下，会默认为每月定投额"""
        balances[0] = self.init_balance
        principals[0] = self.init_balance
        investment_amount[0] = self.init_balance

        for i in range(month_num):
            year_num = i // 12

            # Apply increment to monthly investment or not
            if i % 12 == 0 and self._increment != 0 and \
                    year_num <= self._increment_period and year_num != 0:
                current_monthly_investment += self._increment

            balances[i + 1] = (balances[i] * (1 + excepted_return) +
                               current_monthly_investment)
            principals[i + 1] = principals[i] + current_monthly_investment
            returns[i + 1] = balances[i + 1] - principals[i + 1]
            investment_amount[i + 1] = current_monthly_investment

        """Create monthly data"""
        dates = date_range(
            start= Timestamp.now().to_period("M").to_timestamp(),
            periods=month_num + 1,
            freq='ME'
        )

        monthly_data = DataFrame({
            "Date": dates,
            "Principal": np_round(principals).astype(int),  # 直接转换为整数
            "Return": np_round(returns).astype(int),
            "Balance": np_round(balances).astype(int),
            "Investment": np_round(investment_amount).astype(int)
        })

        return InvestmentResult(
            final_balance=round(balances[-1].item()),  # 对单个数值使用Python内置的round
            total_principal=round(principals[-1].item()),
            total_return=round(returns[-1].item()),
            monthly_data=monthly_data
        )

    def back_to_present(self,
                        target: Literal["amount", "rate", "horizon"],
                        value_target: float,
                        initial: float = None) -> float | ndarray:
        """
        Calculate either required monthly investment or required monthly return
        to reach a target value.
        除了计算出的收益率之外，其余回传的所有结果会向上取整
        除了要传入的数值之外，其余的数值都会使用类中的属性值，如果需要传入其他数值，需要更改类的属性值。

        Parameters:
            target (str): "num" for monthly investment or "rate" for required return
            or "horizon" for required investment horizon.
            value_target (float): Target final balance.

        Returns:
            float: Required monthly investment or monthly return rate
            :param value_target: 目标金额
            :param target: 所求目标类型，amount为每月投资额，rate为年化收益率，horizon为投资期限
            :param initial: 初始值
        """
        #  TODO: 增加其他数值的传入，让用户可以传入其他数值而不用修改类的属性值。
        if value_target <= 0:
            raise ValueError("Target value must be positive")

        month_num = self.horizon * 12
        initial_balance = self.init_balance if initial is None else initial

        if target == "amount":
            # Calculate required monthly investment
            if value_target <= initial_balance:
                return 0  # 已达到目标,无需投资
            # 等比数列求和
            if self.__monthly_return == 0:
                # Special case for 0% return
                amount = (value_target - initial_balance) / month_num
                return math.ceil(amount)
            else:
                numerator = (value_target - initial_balance * pow(1 + self.__monthly_return, month_num))
                denominator = (pow(1 + self.__monthly_return, month_num) - 1) / self.__monthly_return
                amount = numerator / denominator
                return math.ceil(amount)

        elif target == "rate":
            # Calculate required monthly return rate using numerical method
            from scipy.optimize import fsolve
            if value_target <= initial_balance + self.m_investment * month_num:
                return 0

            tolerance = 1e-6  # 设定精度，用于判断是否达到目标值
            left, right = -0.99, 10.0  # 设定二分法的左右边界

            def calc_final_value(r):
                if abs(r) < 1e-10:
                    return initial_balance + self.m_investment * month_num
                return (initial_balance * pow(1 + r, month_num) +
                        self.m_investment * (pow(1 + r, month_num) - 1) / r)

            while right - left > tolerance:
                mid = (left + right) / 2
                final_value = calc_final_value(mid)

                if (final_value - target_value < tolerance) and final_value >= target_value:
                    return mid
                elif final_value < target_value:
                    left = mid
                else:
                    right = mid

            monthly = (left + right) / 2
            annual = pow(1 + monthly, 12) - 1

            return annual

        elif target == "horizon":
            # Calculate required investment horizon using logarithm formula
            if value_target <= initial_balance: # 如果目标值小于初始值，直接返回0
                return 0  # 已达到目标
            # Calculate number of months using the derived formula
            if self.__monthly_return == 0:
                # Special case for 0% return
                months = (value_target - initial_balance) / self.m_investment
            else:
                numerator = value_target + self.m_investment / self.__monthly_return
                denominator = initial_balance + self.m_investment / self.__monthly_return
                months = math.log(numerator / denominator) / math.log(1 + self.__monthly_return)

            # Convert months to years, ensure non-negative and ceiling to next integer
            years = math.ceil(max(0, months / 12))
            return years


if __name__ == "__main__":
    # 使用示例
    try:
        # 创建计算器实例：10%年收益率，5年投资期，每月投资1000元
        calc = InvestmentCalculator(
            y_return=0.02,  # 10% 年收益率
            horizon=10,  # 5年投资期
            m_investment=2,  # 每月投资1000元
            init_balance=0,  # 初始余额0元
            method="geometric",  # 使用几何平均值计算月收益率
            increment=0,  # 每年增加100元投资
            incre_period=0  # 持续3年增
        )

        # 计算最终余额
        final_result = calc.automatic_investment()
        print(f"Final balance after {calc.horizon} years: {final_result.final_balance:.2f}")
        print(f"Total principal invested: {final_result.total_principal:.2f}")
        print(f"Total return: {final_result.total_return:.2f}")

        # 画图
        final_result.monthly_data.plot(x="Date", y=["Principal", "Return", "Balance"])
        plt.show()

        # 计算达到目标所需的每月投资额
        target_value = 1000
        required_monthly = calc.back_to_present("amount", target_value)
        print(f"Required monthly investment to reach {target_value} "
              f"with {calc.y_return} monthly return "
              f"and {calc.init_balance} initial balance : {required_monthly:.2f}")

        # 计算达到目标所需的年化收益率
        required_return = calc.back_to_present("rate", target_value)
        print(f"Reaching the {target_value} target with {calc.m_investment} monthly investment, "
              f"required yearly return rate: {required_return:.4%}")

        # 计算达到目标所需的投资期限
        required_horizon = calc.back_to_present("horizon", target_value)
        print(f"Reaching the {target_value} target with {calc.m_investment} monthly investment, "
              f"required investment horizon: {required_horizon} years")

    except ValueError as e:
        print(f"Error: {e}")
