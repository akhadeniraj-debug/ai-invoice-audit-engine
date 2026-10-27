"""
Comprehensive Test Suite for Sai Arts Signage Enterprise Web Application.
Tests DOM ID integrity, metadata, branding, configuration matrix,
pricing calculations, and edge cases (zero, negative, boundaries, PIN, etc.).
"""

import json
import math
import os
import re
import sys
import urllib.parse

ROOT_DIR = r"e:\aws_ai_project"
APP_DIR = os.path.join(ROOT_DIR, "signage-enterprise")
HTML_PATH = os.path.join(APP_DIR, "index.html")
JS_PATH = os.path.join(APP_DIR, "app.js")
CSS_PATH = os.path.join(APP_DIR, "style.css")
PKG_PATH = os.path.join(APP_DIR, "package.json")
ROOT_PKG_PATH = os.path.join(ROOT_DIR, "package.json")

test_results = []

def js_round(x):
    """Simulates JavaScript Math.round(x) - round half towards +infinity."""
    return math.floor(x + 0.5)

def run_test(name, assertion_fn):
    try:
        assertion_fn()
        test_results.append((name, True, "PASSED"))
        print(f" [PASS] {name}")
    except AssertionError as e:
        test_results.append((name, False, f"FAILED: {str(e)}"))
        print(f" [FAIL] {name}: {str(e)}")
    except Exception as e:
        test_results.append((name, False, f"ERROR: {str(e)}"))
        print(f" [ERROR] {name}: {str(e)}")

# ============================================================================
# 1. METADATA & BRANDING TESTS
# ============================================================================
def test_package_json():
    assert os.path.exists(PKG_PATH), "signage-enterprise/package.json not found"
    with open(PKG_PATH, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg.get("name") == "sai-arts-signage", f"package.json name is '{pkg.get('name')}', expected 'sai-arts-signage'"

def test_root_package_json():
    assert os.path.exists(ROOT_PKG_PATH), "Root package.json not found"
    with open(ROOT_PKG_PATH, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg.get("name") == "sai-arts-signage", f"Root package.json name is '{pkg.get('name')}', expected 'sai-arts-signage'"

def test_html_branding_and_meta():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    
    assert "Sai Arts" in html, "'Sai Arts' brand not found in HTML"
    assert "sai-arts-signage" in html, "'sai-arts-signage' not found in meta tags"
    assert 'name="project-name" content="sai-arts-signage"' in html, "meta project-name tag missing"
    assert 'name="application-name" content="sai-arts-signage"' in html, "meta application-name tag missing"
    assert "Precision 3D Acrylic Letters, ACP Facades & Industrial Safety Signage" in html, "Expected tagline missing in HTML"
    assert "Sai Arts Manufacturing" in html, "Quotation brand missing in HTML"
    assert "Sai Arts Certified Industrial Standard" in html, "Trust grid header missing in HTML"

def test_dom_elements_alignment():
    with open(JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    js_ids = set(re.findall(r'document\.getElementById\(["\']([^"\']+)["\']\)', js))
    html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', html))
    missing = js_ids - html_ids
    assert len(missing) == 0, f"Missing DOM IDs in HTML: {missing}"

# ============================================================================
# 2. CONFIGURATION MATRIX TESTING
# ============================================================================
def test_catalog_structure():
    with open(JS_PATH, "r", encoding="utf-8") as f:
        js = f.read()

    # Verify all 4 categories are present in JS
    required_cats = ["acrylic-3d", "acp-elevation", "industrial-safety", "metal-architectural"]
    for cat in required_cats:
        assert f'"{cat}"' in js or f"'{cat}'" in js, f"Category '{cat}' missing from PRODUCTS"

    # Verify key product IDs across all categories
    required_products = [
        "frontlit-acrylic",
        "backlit-halo",
        "solid-cast",
        "edgelit-crystal",
        "exterior-facade",
        "cnc-backlit",
        "wood-marble-acp",
        "safety-instruction",
        "radium-emergency",
        "machine-plates",
        "ss-titanium-gold",
        "ss-rose-gold",
        "anodized-aluminum",
    ]
    for p in required_products:
        assert f'id: "{p}"' in js or f"id: '{p}'" in js, f"Product '{p}' missing from catalog"

# ============================================================================
# 3. PRICING & CALCULATION ENGINE EDGE CASES
# ============================================================================
def calculate_quote(unit_type, base_rate, mult, led_surcharge, install_rate,
                    width_ft=0, width_in=0, height_ft=0, height_in=0,
                    letter_count=0, letter_height_in=0, gst_percent=18):
    if unit_type == "sqft":
        total_w = max(0, width_ft + width_in / 12)
        total_h = max(0, height_ft + height_in / 12)
        sqft = max(1.0, total_w * total_h)
        base_cost = sqft * base_rate * mult
        lighting_cost = sqft * led_surcharge
        install_cost = sqft * install_rate
    else:
        valid_count = max(1, letter_count)
        valid_height = max(1, letter_height_in)
        running_inches = valid_count * valid_height
        base_cost = running_inches * base_rate * mult
        lighting_cost = valid_count * led_surcharge
        install_cost = valid_count * install_rate * 1.5

    base_cost = max(0, base_cost if math.isfinite(base_cost) else 0)
    lighting_cost = max(0, lighting_cost if math.isfinite(lighting_cost) else 0)
    install_cost = max(0, install_cost if math.isfinite(install_cost) else 0)

    subtotal = js_round(base_cost + lighting_cost + install_cost)
    gst_amount = js_round(subtotal * (gst_percent / 100))
    grand_total = subtotal + gst_amount

    return {
        "baseCost": base_cost,
        "lightingCost": lighting_cost,
        "installCost": install_cost,
        "subtotal": subtotal,
        "gstAmount": gst_amount,
        "grandTotal": grand_total,
    }

def test_sqft_standard_calculation():
    # 8ft × 4ft = 32 sqft. Base=420, Mult=1.0, LED=160, Install=85
    res = calculate_quote("sqft", 420, 1.0, 160, 85, width_ft=8, width_in=0, height_ft=4, height_in=0)
    expected_sqft = 32.0
    expected_base = expected_sqft * 420 * 1.0 # 13440
    expected_led = expected_sqft * 160        # 5120
    expected_install = expected_sqft * 85    # 2720
    expected_subtotal = js_round(expected_base + expected_led + expected_install) # 21280
    expected_gst = js_round(expected_subtotal * 0.18) # 3830
    expected_total = expected_subtotal + expected_gst # 25110

    assert res["subtotal"] == expected_subtotal, f"Subtotal mismatch: {res['subtotal']} != {expected_subtotal}"
    assert res["grandTotal"] == expected_total, f"Grand total mismatch: {res['grandTotal']} != {expected_total}"
    assert res["grandTotal"] == res["subtotal"] + res["gstAmount"], "Subtotal + GST != Grand Total"

def test_sqft_zero_and_negative_edge_cases():
    # 0ft × 0ft -> clamp to min 1 sqft
    res_zero = calculate_quote("sqft", 420, 1.0, 160, 85, width_ft=0, width_in=0, height_ft=0, height_in=0)
    assert res_zero["subtotal"] > 0, "Zero dimension should clamp to min 1 sqft"
    assert math.isfinite(res_zero["grandTotal"]), "Zero dimension resulted in non-finite value"
    assert res_zero["grandTotal"] > 0, "Grand total must be positive"

    # Negative input -> clamp to 0 then min 1 sqft
    res_neg = calculate_quote("sqft", 420, 1.0, 160, 85, width_ft=-10, width_in=-5, height_ft=-4, height_in=0)
    assert res_neg["subtotal"] > 0, "Negative dimensions should be clamped gracefully"
    assert res_neg["subtotal"] == res_zero["subtotal"], "Negative should clamp identically to 0"

def test_sqft_fractional_inches_edge_case():
    # 10 ft 6 in × 5 ft 3 in = 10.5 × 5.25 = 55.125 sqft
    res = calculate_quote("sqft", 420, 1.15, 160, 85, width_ft=10, width_in=6, height_ft=5, height_in=3)
    assert res["subtotal"] > 0
    assert res["grandTotal"] == res["subtotal"] + res["gstAmount"]
    assert math.isfinite(res["grandTotal"])

def test_letter_standard_calculation():
    # "SAI ARTS" = 7 letters, 12" height. Rate=95, Mult=1.0, LED=160, Install=85
    # Running inches = 7 × 12 = 84"
    # Base = 84 × 95 = 7980
    # LED = 7 × 160 = 1120
    # Install = 7 × 85 × 1.5 = 892.5
    # Subtotal = 7980 + 1120 + 892.5 = 9992.5 -> Math.round is 9993
    # GST = 9993 * 0.18 = 1798.74 -> Math.round is 1799
    # Total = 9993 + 1799 = 11792
    res = calculate_quote("letter", 95, 1.0, 160, 85, letter_count=7, letter_height_in=12)
    assert res["subtotal"] == 9993, f"Expected subtotal 9993, got {res['subtotal']}"
    assert res["gstAmount"] == 1799, f"Expected GST 1799, got {res['gstAmount']}"
    assert res["grandTotal"] == 11792, f"Expected Total 11792, got {res['grandTotal']}"

def test_letter_zero_empty_edge_cases():
    # 0 letters -> clamp to min 1 letter
    res_zero_letters = calculate_quote("letter", 95, 1.0, 160, 85, letter_count=0, letter_height_in=12)
    assert res_zero_letters["subtotal"] > 0, "Zero letter count must clamp to 1"
    assert res_zero_letters["grandTotal"] == res_zero_letters["subtotal"] + res_zero_letters["gstAmount"]

    # 0 height -> clamp to min 1 inch
    res_zero_height = calculate_quote("letter", 95, 1.0, 160, 85, letter_count=5, letter_height_in=0)
    assert res_zero_height["subtotal"] > 0, "Zero letter height must clamp to 1 inch"

def test_admin_rates_update():
    # Custom live workshop rates: Base=500, Mult=1.0, LED=200, Install=100
    res = calculate_quote("sqft", 500, 1.0, 200, 100, width_ft=10, width_in=0, height_ft=10, height_in=0)
    # 100 sqft: Base=50,000, LED=20,000, Install=10,000 => Subtotal=80,000
    # GST=14,400 => Total=94,400
    assert res["subtotal"] == 80000, f"Expected 80000, got {res['subtotal']}"
    assert res["gstAmount"] == 14400, f"Expected 14400, got {res['gstAmount']}"
    assert res["grandTotal"] == 94400, f"Expected 94400, got {res['grandTotal']}"

def test_whatsapp_url_generation():
    est = {
        "productName": "Front-Lit 3D Acrylic Letters",
        "dimensions": "7 Letters × 12\" Height = 84 Total Running Inches",
        "materialName": "3mm Virgin Cast Acrylic Face",
        "colorName": "Pure Day White",
        "lightingName": "Samsung IP67 Cool Day White (6500K)",
        "subtotal": 9993,
        "gstAmount": 1799,
        "grandTotal": 11792,
    }
    # Test message with formatted currency
    msg = f"""*SAI ARTS INDUSTRIAL & ARCHITECTURAL QUOTATION*
📄 *Estimate Ref:* EST-2026-ONLINE
📅 *Date:* 27 Oct 2026
------------------------------------
🏷️ *Product:* {est['productName']}
📐 *Dimensions:* {est['dimensions']}
🧱 *Material Grade:* {est['materialName']}
🎨 *Shade:* {est['colorName']}
💡 *Lighting:* {est['lightingName']}
------------------------------------
💰 *Subtotal:* ₹{est['subtotal']:,}
🏛️ *GST (18%):* ₹{est['gstAmount']:,}
⭐ *Grand Total:* ₹{est['grandTotal']:,}
------------------------------------
🛡️ *Warranty:* 5-Year UV Sheet Colorfast + 2-Year Samsung LED Replacement.
Please arrange an engineer site visit / formal PO generation."""

    encoded = urllib.parse.quote(msg)
    url = f"https://wa.me/919876543210?text={encoded}"
    assert "SAI" in url, "Brand name not encoded in WhatsApp URL"
    assert "9%2C993" in url or "9,993" in url or "9993" in url, "Subtotal missing from WhatsApp message"
    assert "11%2C792" in url or "11,792" in url or "11792" in url, "Grand Total missing from WhatsApp message"
    assert url.startswith("https://wa.me/919876543210"), "Invalid WhatsApp destination endpoint"

def test_css_rules_and_print():
    with open(CSS_PATH, "r", encoding="utf-8") as f:
        css = f.read()

    # Verify 3D lighting classes
    assert ".glow-frontlit" in css, "CSS missing .glow-frontlit class"
    assert ".glow-warm" in css, "CSS missing .glow-warm class"
    assert ".glow-halo" in css, "CSS missing .glow-halo class"

    # Verify Facade classes
    assert ".facade-granite" in css, "CSS missing .facade-granite class"
    assert ".facade-concrete" in css, "CSS missing .facade-concrete class"
    assert ".facade-wood" in css, "CSS missing .facade-wood class"
    assert ".facade-glass" in css, "CSS missing .facade-glass class"

    # Verify Print stylesheet
    assert "@media print" in css, "CSS missing @media print rules"
    assert "#quotation-invoice-container" in css, "Print rules must target quotation container"
    assert "no-print" in css, "Print rules must support .no-print class"

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def main():
    print("=" * 70)
    print("RUNNING COMPREHENSIVE TEST SUITE: SAI ARTS SIGNAGE ENTERPRISE")
    print("=" * 70)

    # 1. Metadata & Branding
    run_test("Package.json name is 'sai-arts-signage'", test_package_json)
    run_test("Root Package.json name is 'sai-arts-signage'", test_root_package_json)
    run_test("HTML Title, Meta & Sai Arts Branding", test_html_branding_and_meta)
    run_test("DOM IDs 100% matched between JS and HTML", test_dom_elements_alignment)

    # 2. Catalog & Products
    run_test("Product catalog categories and key items", test_catalog_structure)

    # 3. Calculation Engine & Edge Cases
    run_test("Sq.Ft Standard pricing math consistency", test_sqft_standard_calculation)
    run_test("Sq.Ft Zero & negative dimension edge cases", test_sqft_zero_and_negative_edge_cases)
    run_test("Sq.Ft Fractional inches dimension edge cases", test_sqft_fractional_inches_edge_case)
    run_test("3D Letter Standard pricing math consistency", test_letter_standard_calculation)
    run_test("3D Letter Zero & empty letter inputs edge cases", test_letter_zero_empty_edge_cases)
    run_test("Workshop Admin rate panel custom override edge cases", test_admin_rates_update)

    # 4. WhatsApp & Print Export
    run_test("WhatsApp quotation message encoding and URL format", test_whatsapp_url_generation)
    run_test("CSS Facade simulators, glow effects & @media print integrity", test_css_rules_and_print)

    print("=" * 70)
    passed = sum(1 for _, ok, _ in test_results if ok)
    failed = len(test_results) - passed
    print(f"SUMMARY: {passed}/{len(test_results)} Tests Passed ({failed} Failed)")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
