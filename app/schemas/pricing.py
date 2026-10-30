"""Pydantic schemas for protected pricing and quote calculation engine."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class PricingCalculationRequest(BaseModel):
    """Input payload for dynamic signage and elevation pricing calculation."""

    unit_type: Literal["sqft", "letter"] = Field(..., description="Calculation unit basis: 'sqft' for panels or 'letter' for 3D channel letters")
    product_name: str = Field(default="Front-Lit 3D Acrylic Letters", description="Product or signage specification name")
    material_name: str = Field(default="3mm Virgin Cast Acrylic Face", description="Substrate or material grade description")
    material_multiplier: float = Field(default=1.0, ge=0.1, le=10.0, description="Material thickness / grade pricing multiplier")
    lighting_name: str = Field(default="Samsung IP67 Cool Day White (6500K)", description="Illumination / LED module selection")
    lighting_surcharge: float = Field(default=160.0, ge=0.0, description="LED / SMPS surcharge per unit in INR")
    color_name: str = Field(default="Pure Day White", description="Architectural color swatch or shade name")

    # Dimensions for sqft calculations
    width_ft: float = Field(default=8.0, ge=0.0, description="Width in feet")
    width_in: float = Field(default=0.0, ge=0.0, le=11.99, description="Width in inches")
    height_ft: float = Field(default=4.0, ge=0.0, description="Height in feet")
    height_in: float = Field(default=0.0, ge=0.0, le=11.99, description="Height in inches")

    # Dimensions for letter calculations
    letter_height_in: float = Field(default=12.0, ge=1.0, le=100.0, description="Letter height in inches")
    letter_count: int = Field(default=7, ge=1, le=1000, description="Number of 3D letters")
    text: Optional[str] = Field(default="SAI ARTS", description="Display / branding text for the sign")

    # Base Rates
    base_sqft_rate: float = Field(default=420.0, ge=0.0, description="Base fabrication rate per sq.ft in INR")
    base_letter_rate: float = Field(default=95.0, ge=0.0, description="Base fabrication rate per running inch in INR")
    installation_rate: float = Field(default=85.0, ge=0.0, description="Base installation / scaffolding rate per unit in INR")
    gst_percent: float = Field(default=18.0, ge=0.0, le=100.0, description="Applicable GST percentage (standard 18%)")


class PricingCalculationResponse(BaseModel):
    """Detailed deterministic quotation and pricing breakdown response."""

    unit_type: str
    product_name: str
    material_name: str
    lighting_name: str
    color_name: str
    dimensions_summary: str
    total_units: float = Field(..., description="Computed total sq.ft area or running inches")
    base_cost: float
    lighting_cost: float
    installation_cost: float
    subtotal: float
    gst_percent: float
    gst_amount: float
    grand_total: float
    currency: str = "INR"
    client_name: Optional[str] = None
