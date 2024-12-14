# api/index.py
import logging
import os
from flask_cors import CORS
from flask import Flask, json, jsonify, request
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.investment_calculator import InvestmentCalculator

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

logger = logging.getLogger(__name__)

PRESENT_METHOD = {
    "amount": "amount",
    "rate": "rate",
    "horizon": "horizon"
}


@app.route("/api/test", methods=["GET"])
def test_route():
    return jsonify({"message": "Test successful!"})


@app.route("/api/final_balance", methods=["POST"])
def get_final_balance():
    json_data = request.get_json()
    year_return = float(json_data.get("year_return", 0)) / 100  # 年收益率
    monthly_reserve = float(json_data.get("monthly_reserve", 0))  # 每月投资额度
    initial_investment = float(json_data.get("initial_investment", 0))
    reserve_periods = int(json_data.get("reserve_periods", 0))
    increment = float(json_data.get("increment", 0))
    incre_period = int(json_data.get("incre_period", 0))

    calc = InvestmentCalculator(
        y_return=year_return,  # 10% 年收益率
        horizon=reserve_periods,  # 5年投资期
        m_investment=monthly_reserve,  # 每月投资1000元
        init_balance=initial_investment,  # 初始余额0元
        method="geometric",  # 使用几何平均值计算月收益率
        increment=increment,
        incre_period=incre_period
    )

    data = calc.automatic_investment()
    result = {
        "final_balance": data.final_balance,
        "total_principal": data.total_principal,
        "total_return": data.total_return,
        "monthly_data": json.loads(data.monthly_data.to_json(orient="records"))
    }

    response = jsonify({"result": result})
    return response


@app.route("/api/present_data", methods=["POST"])
def get_back_to_present():
    present_method = request.args.get("target")
    logger.debug(f"=======present_method======{present_method}")
    json_data = request.get_json()

    year_return = float(json_data.get("year_return", 0)) / 100  # 年收益率
    monthly_reserve = float(json_data.get("monthly_reserve", 0))  # 每月投资额度
    initial_investment = float(json_data.get("initial_investment", 0))
    reserve_periods = int(json_data.get("reserve_periods", 1))
    increment = float(json_data.get("increment", 0))
    incre_period = int(json_data.get("incre_period", 0))
    target_amount = int(json_data.get("target_amount", 0))

    calc = InvestmentCalculator(
        y_return=year_return,  # 10% 年收益率
        horizon=reserve_periods,  # 5年投资期
        m_investment=monthly_reserve,  # 每月投资1000元
        init_balance=initial_investment,  # 初始余额0元
        method="geometric",  # 使用几何平均值计算月收益率
        increment=increment,
        incre_period=incre_period
    )

    # 目標金額を達成するには
    # target_amount = 1000000
    back_to_present = None
    # chart 用数据
    data = None
    if present_method == PRESENT_METHOD["amount"]:
        back_to_present = calc.back_to_present(present_method, target_amount)
        data = calc.automatic_investment(m_investment=back_to_present)

    if present_method == PRESENT_METHOD["rate"]:
        result = calc.back_to_present(present_method, target_amount)
        back_to_present = round(result, 2) * 100
        data = calc.automatic_investment(annual_rate=result)

    if present_method == PRESENT_METHOD["horizon"]:
        back_to_present = calc.back_to_present(present_method, target_amount)
        # logger.debug(f"=======back_to_present==horizon===={back_to_present}")
        data = calc.automatic_investment(horizon=back_to_present)

    result = {
        "final_balance": data.final_balance,
        "total_principal": data.total_principal,
        "total_return": data.total_return,
        "monthly_data": json.loads(data.monthly_data.to_json(orient="records"))
    }

    responese = jsonify({
        "chart_data": result,
        "back_to_present": back_to_present
    })

    return responese


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
