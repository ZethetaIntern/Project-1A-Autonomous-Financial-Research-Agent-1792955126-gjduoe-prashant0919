"""Safe calculator and advanced financial calculation engine for research analysis."""

import math
import operator
from typing import Any

_OPERATIONS = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
}


def calculate(
    operation: str,
    a: float,
    b: float,
) -> dict[str, Any]:
    """Calculate a basic arithmetic operation."""
    if operation not in _OPERATIONS:
        raise ValueError(f"Unsupported operation: {operation}")

    if not math.isfinite(a) or not math.isfinite(b):
        raise ValueError("Inputs must be finite numbers.")

    if operation == "divide" and b == 0:
        raise ValueError("Cannot divide by zero.")

    result = _OPERATIONS[operation](a, b)

    if not math.isfinite(result):
        raise ValueError("Calculation produced a non-finite result.")

    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result,
    }


def calculate_dcf(
    cash_flows: list[float],
    discount_rate: float,
    terminal_growth_rate: float = 0.025,
) -> dict[str, Any]:
    """Perform Discounted Cash Flow (DCF) valuation with intermediate steps.

    Args:
        cash_flows: Projected free cash flows (e.g. for years 1 through N).
        discount_rate: WACC (e.g. 0.085 for 8.5%).
        terminal_growth_rate: Long-term perpetual growth rate (e.g. 0.025 for 2.5%).
    """
    if not cash_flows or any(not math.isfinite(cf) for cf in cash_flows):
        raise ValueError("cash_flows must be a non-empty list of finite numbers")
    if discount_rate <= terminal_growth_rate:
        raise ValueError("discount_rate must be greater than terminal_growth_rate")

    pv_cash_flows = []
    discounted_sum = 0.0

    for year, cf in enumerate(cash_flows, start=1):
        pv = cf / ((1.0 + discount_rate) ** year)
        pv_cash_flows.append({
            "year": year,
            "fcf": cf,
            "discount_factor": round(1.0 / ((1.0 + discount_rate) ** year), 4),
            "present_value": round(pv, 2),
        })
        discounted_sum += pv

    # Terminal Value calculation (Gordon Growth Model)
    last_cf = cash_flows[-1]
    terminal_fcf = last_cf * (1.0 + terminal_growth_rate)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
    pv_terminal_value = terminal_value / ((1.0 + discount_rate) ** len(cash_flows))

    enterprise_value = discounted_sum + pv_terminal_value

    return {
        "discount_rate_wacc": discount_rate,
        "terminal_growth_rate": terminal_growth_rate,
        "projection_periods": len(cash_flows),
        "pv_explicit_cash_flows": round(discounted_sum, 2),
        "terminal_value": round(terminal_value, 2),
        "pv_terminal_value": round(pv_terminal_value, 2),
        "enterprise_value": round(enterprise_value, 2),
        "terminal_value_share_pct": round((pv_terminal_value / enterprise_value) * 100, 2),
        "intermediate_steps": pv_cash_flows,
    }


def calculate_cagr(
    start_value: float,
    end_value: float,
    periods: float,
) -> dict[str, Any]:
    """Compute Compound Annual Growth Rate (CAGR)."""
    if start_value <= 0 or end_value <= 0:
        raise ValueError("start_value and end_value must be positive for CAGR")
    if periods <= 0:
        raise ValueError("periods must be greater than zero")

    cagr = (end_value / start_value) ** (1.0 / periods) - 1.0
    return {
        "start_value": start_value,
        "end_value": end_value,
        "periods": periods,
        "cagr": round(cagr, 4),
        "cagr_percentage": f"{round(cagr * 100, 2)}%",
    }


def calculate_financial_ratios(inputs: dict[str, Any]) -> dict[str, Any]:
    """Calculate key financial ratios from balance sheet and income statement items."""
    ratios: dict[str, Any] = {}

    revenue = inputs.get("revenue")
    net_income = inputs.get("net_income")
    operating_income = inputs.get("operating_income")
    shareholders_equity = inputs.get("shareholders_equity")
    total_assets = inputs.get("total_assets")
    total_debt = inputs.get("total_debt")
    current_assets = inputs.get("current_assets")
    current_liabilities = inputs.get("current_liabilities")

    if revenue and revenue > 0:
        if operating_income is not None:
            ratios["operating_margin"] = round(operating_income / revenue, 4)
            ratios["operating_margin_pct"] = f"{round((operating_income / revenue) * 100, 2)}%"
        if net_income is not None:
            ratios["net_profit_margin"] = round(net_income / revenue, 4)
            ratios["net_profit_margin_pct"] = f"{round((net_income / revenue) * 100, 2)}%"

    if shareholders_equity and shareholders_equity > 0:
        if net_income is not None:
            ratios["roe"] = round(net_income / shareholders_equity, 4)
            ratios["roe_pct"] = f"{round((net_income / shareholders_equity) * 100, 2)}%"
        if total_debt is not None:
            ratios["debt_to_equity"] = round(total_debt / shareholders_equity, 4)

    if total_assets and total_assets > 0 and net_income is not None:
        ratios["roa"] = round(net_income / total_assets, 4)
        ratios["roa_pct"] = f"{round((net_income / total_assets) * 100, 2)}%"

    if current_liabilities and current_liabilities > 0 and current_assets is not None:
        ratios["current_ratio"] = round(current_assets / current_liabilities, 4)

    return {
        "inputs": inputs,
        "computed_ratios": ratios,
        "status": "success",
    }


def calculation_engine(
    calculation_type: str,
    inputs: dict[str, Any],
) -> dict[str, Any]:
    """Execute high-precision financial calculations with explicit intermediate steps."""
    calc_type = calculation_type.strip().lower()

    if calc_type == "dcf":
        return calculate_dcf(
            cash_flows=inputs["cash_flows"],
            discount_rate=float(inputs["discount_rate"]),
            terminal_growth_rate=float(inputs.get("terminal_growth_rate", 0.025)),
        )

    if calc_type in ("cagr", "growth_rate"):
        return calculate_cagr(
            start_value=float(inputs["start_value"]),
            end_value=float(inputs["end_value"]),
            periods=float(inputs["periods"]),
        )

    if calc_type in ("ratios", "margin_analysis"):
        return calculate_financial_ratios(inputs)

    if calc_type == "arithmetic":
        return calculate(
            operation=inputs["operation"],
            a=float(inputs["a"]),
            b=float(inputs["b"]),
        )

    raise ValueError(f"Unsupported calculation_type: {calculation_type}")
