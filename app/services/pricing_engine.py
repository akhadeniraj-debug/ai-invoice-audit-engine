"""Deterministic pricing and itemized quotation calculation engine for Sai Arts signage."""

import math
from typing import Dict, Any

from app.schemas.pricing import PricingCalculationRequest, PricingCalculationResponse


def js_round(val: float) -> int:
    """Standard commercial round-half-up (equivalent to JavaScript Math.round)."""
    return math.floor(val + 0.5)


class PricingEngine:
    """Calculates deterministic fabrication costs, GST, and itemized quotations."""

    @classmethod
    def calculate(cls, req: PricingCalculationRequest, client_name: str = None) -> PricingCalculationResponse:
        """Computes subtotal, taxes, and final pricing based on unit type and material specifications."""
        if req.unit_type == "sqft":
            total_w = max(0.0, req.width_ft + (req.width_in / 12.0))
            total_h = max(0.0, req.height_ft + (req.height_in / 12.0))
            sqft = max(1.0, total_w * total_h)

            base_cost = sqft * req.base_sqft_rate * req.material_multiplier
            lighting_cost = sqft * req.lighting_surcharge
            installation_cost = sqft * req.installation_rate
            total_units = round(sqft, 2)
            dimensions_summary = f"{req.width_ft} ft {req.width_in} in (W) × {req.height_ft} ft {req.height_in} in (H) = {sqft:.2f} Sq.Ft"
        else:
            # 3D Letter Unit
            valid_count = max(1, req.letter_count)
            valid_height = max(1.0, req.letter_height_in)
            running_inches = valid_count * valid_height

            base_cost = running_inches * req.base_letter_rate * req.material_multiplier
            lighting_cost = valid_count * req.lighting_surcharge
            installation_cost = valid_count * req.installation_rate * 1.5
            total_units = float(running_inches)
            dimensions_summary = f"{valid_count} Letters × {valid_height:.0f}\" Height = {running_inches:.0f} Total Running Inches"

        subtotal = js_round(base_cost + lighting_cost + installation_cost)
        gst_amount = js_round(subtotal * (req.gst_percent / 100.0))
        grand_total = subtotal + gst_amount

        return PricingCalculationResponse(
            unit_type=req.unit_type,
            product_name=req.product_name,
            material_name=req.material_name,
            lighting_name=req.lighting_name,
            color_name=req.color_name,
            dimensions_summary=dimensions_summary,
            total_units=total_units,
            base_cost=round(base_cost, 2),
            lighting_cost=round(lighting_cost, 2),
            installation_cost=round(installation_cost, 2),
            subtotal=float(subtotal),
            gst_percent=req.gst_percent,
            gst_amount=float(gst_amount),
            grand_total=float(grand_total),
            currency="INR",
            client_name=client_name,
        )
