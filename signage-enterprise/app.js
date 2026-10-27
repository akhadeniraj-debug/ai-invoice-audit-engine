/**
 * ApexSign Industrial & Architectural Signage Enterprise
 * Product Catalog, Dynamic Dimension & Material Estimator, and WhatsApp Quotation Engine.
 */

// ============================================================================
// CONFIGURATION ENGINE: PRODUCTS, MATERIALS, SHADES & WARRANTY DEFINITIONS
// (Easily editable config object: Add or update materials in seconds)
// ============================================================================
const PRODUCTS = {
  "acrylic-3d": {
    categoryName: "Acrylic & 3D LED Letters",
    categoryDescription: "Precision laser-cut virgin cast acrylic channel letters with Samsung/Osram IP67 illuminated modules.",
    items: [
      {
        id: "frontlit-acrylic",
        name: "Front-Lit 3D Acrylic Letters",
        tagline: "High-impact illumination with uniform face glow and aluminum/SS return rims",
        unitType: "letter", // "letter" or "sqft"
        baseRate: 95, // in ₹ per running inch
        image: "https://images.unsplash.com/photo-1542744095-291d1f67b221?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acrylic/frontlit-1.jpg",
        warranty: {
          sheet: "5-Year UV Anti-Yellowing Guarantee",
          led: "2-Year Samsung Direct Replacement",
          powerSupply: "2-Year Rainproof Meanwell Warranty",
        },
        specs: [
          { label: "Face Material", value: "Cast Virgin Grade Acrylic (A-Cast / Astari)" },
          { label: "Return Rim", value: "Powder Coated Aluminum / SS 304 Channel (2.5\" - 4\" Depth)" },
          { label: "Back Base", value: "10mm High-Density Waterproof PVC Foam Sheet" },
          { label: "LED Modules", value: "Samsung IP67 Injection Molded 160° Optical Lens (1.2W)" },
          { label: "SMPS Driver", value: "Meanwell / Rainproof Industrial Grade 12V DC" },
        ],
        materialGrades: [
          { id: "cast-3mm", name: "3mm Virgin Cast Acrylic Face", multiplier: 1.0, desc: "Standard commercial outdoor signage grade" },
          { id: "cast-5mm", name: "5mm Heavy-Duty Cast Acrylic Face", multiplier: 1.15, desc: "High wind-load and large architectural letters" },
          { id: "cast-8mm", name: "8mm Solid Carved Architectural Face", multiplier: 1.35, desc: "Ultra-premium depth with diamond polished returns" },
        ],
        lightingOptions: [
          { id: "samsung-6500k", name: "Samsung IP67 Cool Day White (6500K)", surcharge: 160, glowClass: "glow-frontlit" },
          { id: "osram-3000k", name: "Osram IP67 Warm Architectural (3000K)", surcharge: 180, glowClass: "glow-warm" },
          { id: "samsung-4000k", name: "Samsung Natural Neutral White (4000K)", surcharge: 170, glowClass: "glow-frontlit" },
          { id: "non-lit", name: "Non-Lit (Ambient Day/Room Light)", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "backlit-halo",
        name: "Back-Lit / Halo Glow 3D Letters",
        tagline: "Subtle architectural luxury with floating wall-wash halo lighting",
        unitType: "letter",
        baseRate: 115,
        image: "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acrylic/backlit-1.jpg",
        warranty: {
          sheet: "5-Year Colorfast Grade 304 / Acrylic Guarantee",
          led: "2-Year IP67 Full Replacement Warranty",
          powerSupply: "2-Year Industrial SMPS Warranty",
        },
        specs: [
          { label: "Face Material", value: "Stainless Steel 304 Titanium PVD / Cast Acrylic" },
          { label: "Illumination Type", value: "Rear Projected Diffused Halo Wall Wash" },
          { label: "Mounting System", value: "Stainless Steel Concealed Standoff Spacers (1.5\" Gap)" },
          { label: "LED Modules", value: "Osram / Samsung Waterproof High-Density Back-Glow" },
        ],
        materialGrades: [
          { id: "ss304-halo", name: "SS 304 Titanium Face + Acrylic Backer", multiplier: 1.0, desc: "Luxury corporate entrance standard" },
          { id: "acrylic-halo", name: "Opaque Cast Acrylic Face + Frost Base", multiplier: 0.95, desc: "Modern architectural minimalist styling" },
        ],
        lightingOptions: [
          { id: "osram-3000k", name: "Osram IP67 Warm Architectural (3000K)", surcharge: 190, glowClass: "glow-warm" },
          { id: "samsung-6500k", name: "Samsung IP67 Cool White (6500K)", surcharge: 170, glowClass: "glow-frontlit" },
          { id: "amber-gold", name: "Golden Amber Halo Glow (2400K)", surcharge: 210, glowClass: "glow-warm" },
        ],
      },
      {
        id: "solid-cast",
        name: "Solid Block Cast Acrylic Letters",
        tagline: "Heavy-gauge solid acrylic CNC machined letters for high-end interior lobbies",
        unitType: "letter",
        baseRate: 75,
        image: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acrylic/solid-1.jpg",
        warranty: {
          sheet: "10-Year Indoor Zero-Discoloration Warranty",
          led: "N/A (Non-Lit Solid Architectural Block)",
          powerSupply: "N/A",
        },
        specs: [
          { label: "Material Composition", value: "100% Virgin Mitsubishi/Perspex Cast Acrylic" },
          { label: "Cutting Method", value: "High-Precision 3-Axis CNC Carving & Flame Polished Edges" },
          { label: "Installation", value: "3M VHB Industrial Structural Adhesive Tape + Stud Pins" },
        ],
        materialGrades: [
          { id: "solid-8mm", name: "8mm Solid Cast Acrylic Block", multiplier: 1.0, desc: "Executive door and boardroom signage" },
          { id: "solid-12mm", name: "12mm Solid Cast Acrylic Block", multiplier: 1.35, desc: "Heavy lobby reception wall branding" },
          { id: "solid-20mm", name: "20mm Monumental Solid Cast Block", multiplier: 1.85, desc: "Ultra-heavy solid depth architectural letters" },
        ],
        lightingOptions: [
          { id: "non-lit", name: "Non-Lit (Solid Monolithic Acrylic)", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "edgelit-crystal",
        name: "Crystal Edge-Lit Acrylic Signage",
        tagline: "Laser-dotted Light Guide Plate (LGP) offering ultra-slim 8mm profile with crystal-clear edges",
        unitType: "sqft",
        baseRate: 650,
        image: "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acrylic/edgelit-1.jpg",
        warranty: {
          sheet: "5-Year Optical Light Guide Guarantee",
          led: "2-Year High-CRI Strip Replacement",
          powerSupply: "2-Year Slimline Adapter Warranty",
        },
        specs: [
          { label: "Optical Core", value: "Laser V-Groove Dotted PMMA Light Guide Panel" },
          { label: "Frame Assembly", value: "Snap-Open Anodized Aluminum Extrusion (18mm Thin)" },
          { label: "LED Integration", value: "High-CRI 90+ Perimeter Ribbon LEDs with Heat-Sink" },
        ],
        materialGrades: [
          { id: "edgelit-single", name: "Single-Sided Slimline Crystal Box (18mm)", multiplier: 1.0, desc: "Wall-mounted slim architectural lightbox" },
          { id: "edgelit-double", name: "Double-Sided Suspended Crystal Panel (24mm)", multiplier: 1.55, desc: "Ceiling-hung glass entrance directories" },
        ],
        lightingOptions: [
          { id: "samsung-6500k", name: "Perimeter Cool White 6500K LGP", surcharge: 250, glowClass: "glow-frontlit" },
          { id: "osram-3000k", name: "Perimeter Warm White 3000K LGP", surcharge: 270, glowClass: "glow-warm" },
        ],
      },
    ],
  },

  "acp-elevation": {
    categoryName: "ACP & Elevation Facade Work",
    categoryDescription: "Aluminum Composite Panel structural elevation cladding and CNC stencil router-cut illumination boards.",
    items: [
      {
        id: "exterior-facade",
        name: "Exterior ACP Facade Cladding & Paneling",
        tagline: "Architectural grade exterior facade cladding with corrosion-proof MS subframe",
        unitType: "sqft",
        baseRate: 380, // in ₹ per sq.ft
        image: "https://images.unsplash.com/photo-1504307651254-35680f356dfd?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acp/facade-1.jpg",
        warranty: {
          sheet: "10-Year Alubond/Eurobond PVDF Coating Warranty",
          structural: "15-Year Subframe Structural Rigidity",
          sealant: "5-Year Weatherproof Dow Corning Silicone Seal",
        },
        specs: [
          { label: "Sheet Brand", value: "Eurobond / Aludecor / Alstrong Architectural Series" },
          { label: "Coating Type", value: "Kynar 500 PVDF Fluorocarbon 2-Coat System" },
          { label: "Aluminum Skin", value: "0.25mm / 0.50mm Marine-Grade Alloy Skin" },
          { label: "Sub-Structure", value: "1.5\" x 1.5\" Heavy-Gauge 16G Mild Steel Box Frame with Anti-Rust Zinc Chromate" },
          { label: "Joint Sealing", value: "Dow Corning 789 Weatherproofing Architectural Neutral Silicone" },
        ],
        materialGrades: [
          { id: "acp-3mm-ext", name: "3mm Exterior PVDF Grade ACP (0.25mm Coil)", multiplier: 1.0, desc: "Standard commercial elevation and shopfronts" },
          { id: "acp-4mm-heavy", name: "4mm Heavy-Duty PVDF ACP (0.50mm Coil)", multiplier: 1.35, desc: "Industrial high-rise towers and heavy wind zones" },
          { id: "acp-4mm-fr", name: "4mm Fire-Retardant FR Grade (Class B1/A2)", multiplier: 1.75, desc: "Corporate tech parks, airports, and hospitals" },
        ],
        lightingOptions: [
          { id: "non-lit", name: "Non-Lit Cladding (Daylight Facade)", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "cnc-backlit",
        name: "CNC Router-Cut Backlit ACP Signboard",
        tagline: "Precision stencil router-routed signage with seamless internal acrylic inlay",
        unitType: "sqft",
        baseRate: 520,
        image: "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acp/cnc-1.jpg",
        warranty: {
          sheet: "10-Year PVDF Colorfast Guarantee",
          led: "2-Year Samsung Module Replacement",
          powerSupply: "2-Year Industrial SMPS Warranty",
        },
        specs: [
          { label: "Base Panel", value: "4mm Exterior PVDF Coated ACP (Aludecor)" },
          { label: "Stencil Inlay", value: "3mm Virgin Cast White / Color Acrylic Inlay" },
          { label: "Internal Frame", value: "1.25\" MS Tube Frame with GI Backtray" },
          { label: "LED Illumination", value: "Samsung IP67 Injection Lens Modules" },
        ],
        materialGrades: [
          { id: "cnc-flat", name: "Flush Acrylic Stencil Inlay (Flat Cut)", multiplier: 1.0, desc: "Clean modern flat illuminated letter effect" },
          { id: "cnc-emboss-10mm", name: "10mm 3D Push-Through Acrylic Inlay", multiplier: 1.45, desc: "Letters physically extrude 10mm from ACP face" },
        ],
        lightingOptions: [
          { id: "samsung-6500k", name: "Samsung IP67 6500K Cool White", surcharge: 220, glowClass: "glow-frontlit" },
          { id: "osram-3000k", name: "Osram IP67 3000K Warm Architectural", surcharge: 240, glowClass: "glow-warm" },
        ],
      },
      {
        id: "wood-marble-acp",
        name: "Timber & Marble Series ACP Cladding",
        tagline: "Natural Italian marble & Teak wood grain textures without structural stone weight",
        unitType: "sqft",
        baseRate: 460,
        image: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/acp/wood-1.jpg",
        warranty: {
          sheet: "12-Year Texture Fade-Resistant Guarantee",
          structural: "15-Year Subframe Stability",
        },
        specs: [
          { label: "Texture Finish", value: "Natural Teak / Walnut Wood & Calacatta Marble UV Textured Film" },
          { label: "Panel Thickness", value: "4mm High-Tensile Mineral Core" },
          { label: "Weather Resistance", value: "Zero Rotting, Termite-Proof, Weatherproof PVDF Shield" },
        ],
        materialGrades: [
          { id: "wood-standard", name: "4mm Premium Timber Woodgrain Series", multiplier: 1.0, desc: "Resort, villa, and corporate elevation warmth" },
          { id: "marble-luxury", name: "4mm Italian Calacatta Marble Series", multiplier: 1.15, desc: "High-end corporate entrance & hotel facades" },
        ],
        lightingOptions: [
          { id: "non-lit", name: "Non-Lit Cladding Surface", surcharge: 0, glowClass: "" },
        ],
      },
    ],
  },

  "industrial-safety": {
    categoryName: "Industrial Safety & Statutory Compliance",
    categoryDescription: "OSHA, ISO 7010, and Factory Act compliant safety signboards, evacuation maps, and equipment warning plates.",
    items: [
      {
        id: "safety-instruction",
        name: "Mandatory PPE & Factory Warning Boards",
        tagline: "Factory Act & OSHA compliant mandatory visual instruction signboards for heavy industrial plant floors",
        unitType: "sqft",
        baseRate: 280,
        image: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/safety/ppe-1.jpg",
        warranty: {
          sheet: "5-Year Chemical & UV Surface Guarantee",
          print: "5-Year Anti-Fade Industrial Solvent Ink",
        },
        specs: [
          { label: "Substrate", value: "3mm High-Impact Rigid PVC Foam / 3mm Industrial ACP" },
          { label: "Printing Standard", value: "Direct UV Flatbed Print with Scratch-Proof Matt Over-Laminate" },
          { label: "Compliance Code", value: "IS 9457 / ISO 7010 Graphical Safety Symbols" },
          { label: "Chemical Resistance", value: "Resistant to Diesel, Engine Oil, Mild Acids, and Washing" },
        ],
        materialGrades: [
          { id: "safety-pvc-3mm", name: "3mm Rigid Industrial PVC Board", multiplier: 1.0, desc: "Indoor factory floors, workshops, and assembly lines" },
          { id: "safety-acp-3mm", name: "3mm Industrial Heavy ACP", multiplier: 1.25, desc: "Outdoor yards, chemical tank farms, and docks" },
        ],
        lightingOptions: [
          { id: "non-lit", name: "Standard Non-Lit Matt Coated", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "radium-emergency",
        name: "3M Retro-Reflective Emergency & Road Signs",
        tagline: "3M Diamond Grade reflective sheeting for zero-power nighttime hazard visibility and internal plant roads",
        unitType: "sqft",
        baseRate: 490,
        image: "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/safety/radium-1.jpg",
        warranty: {
          sheet: "7-Year 3M Certified Retro-Reflectivity",
          plate: "10-Year Rust-Proof Aluminum Backing",
        },
        specs: [
          { label: "Reflective Film", value: "3M Diamond Grade DG3 / High Intensity Prismatic (HIP)" },
          { label: "Backing Plate", value: "1.6mm / 2.0mm Heavy Gauge Tempered Aluminum Plate" },
          { label: "Reflectivity Standard", value: "IRC:67-2012 & ASTM D4956 Type XI Certification" },
          { label: "Border Engineering", value: "Folded Safety Edges with Anti-Corrosion Zinc Plated Clamps" },
        ],
        materialGrades: [
          { id: "3m-hip", name: "3M High Intensity Prismatic (Type IV)", multiplier: 1.0, desc: "Factory transit roads, loading docks, and warehouse bays" },
          { id: "3m-diamond", name: "3M Diamond Grade DG3 (Type XI)", multiplier: 1.45, desc: "Critical chemical hazards, rail crossings, and highways" },
        ],
        lightingOptions: [
          { id: "non-lit", name: "Passive Retro-Reflective (Glows in Vehicle Headlights)", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "machine-plates",
        name: "Chemical-Etched SS & Anodized Machine Plates",
        tagline: "Permanent asset tags, machine instruction plates, and electrical hazard nameplates",
        unitType: "sqft",
        baseRate: 680,
        image: "https://images.unsplash.com/photo-1581092335397-9583fe92d232?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/safety/plates-1.jpg",
        warranty: {
          etching: "Lifetime Acid-Etched Text Permanence",
          material: "10-Year Grade 304 Rust-Free Certification",
        },
        specs: [
          { label: "Substrate Grade", value: "Stainless Steel 304 / Hard-Anodized Aluminum (1.0mm - 2.0mm)" },
          { label: "Process", value: "Deep Chemical Acid Etching with Baked Enamel Paint Fill" },
          { label: "Durability", value: "Immune to Solvents, Machine Coolant, Grease, and Extreme Heat" },
        ],
        materialGrades: [
          { id: "ss304-etched", name: "1.2mm SS 304 Deep Chemical Etched", multiplier: 1.0, desc: "Heavy machinery, boilers, and turbine rating plates" },
          { id: "aluminum-anodized", name: "1.5mm Anodized Black Screen Aluminum", multiplier: 0.85, desc: "Control panels, server racks, and CNC stations" },
        ],
        lightingOptions: [
          { id: "non-lit", name: "Non-Lit Etched Metal Plate", surcharge: 0, glowClass: "" },
        ],
      },
    ],
  },

  "metal-architectural": {
    categoryName: "Stainless Steel & Architectural Metals",
    categoryDescription: "Marine-grade Grade 304/316 Stainless Steel with PVD Titanium coatings for luxury hospitality and corporate headquarters.",
    items: [
      {
        id: "ss-titanium-gold",
        name: "Grade 304 Titanium Gold Architectural Letters",
        tagline: "PVD vacuum coated titanium gold in high-gloss mirror or subtle satin hairline finish",
        unitType: "letter",
        baseRate: 135,
        image: "https://images.unsplash.com/photo-1497215728101-856f4ea42174?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/metal/gold-1.jpg",
        warranty: {
          pvdCoating: "10-Year Zero-Peel PVD Titanium Guarantee",
          steel: "Lifetime Grade 304 Rust-Free Certification",
        },
        specs: [
          { label: "Steel Specification", value: "Jindal Grade 304 Non-Magnetic Stainless Steel (1.2mm Face)" },
          { label: "Coating Process", value: "Physical Vapor Deposition (PVD) Titanium Nitride" },
          { label: "Return Depth", value: "Hand-Fabricated 2\" to 4\" Depth Returns with Laser Welded Joints" },
          { label: "Finish Options", value: "High-Reflective Mirror Gold or Architectural Hairline Satin" },
        ],
        materialGrades: [
          { id: "ss-mirror-gold", name: "SS 304 Mirror Gold Titanium PVD", multiplier: 1.0, desc: "Ultra-luxury hotel entrances, jewelers, and corporate towers" },
          { id: "ss-hairline-gold", name: "SS 304 Hairline Satin Gold PVD", multiplier: 1.05, desc: "Architectural satin finish; hides fingerprints and glares" },
        ],
        lightingOptions: [
          { id: "osram-3000k", name: "Osram IP67 Warm Amber Halo Wall Wash", surcharge: 210, glowClass: "glow-warm" },
          { id: "samsung-6500k", name: "Samsung IP67 Cool White Halo Projection", surcharge: 190, glowClass: "glow-frontlit" },
          { id: "non-lit", name: "Non-Lit Solid Titanium Metal", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "ss-rose-gold",
        name: "Rose Gold & Antique Bronze Metal Letters",
        tagline: "Warm contemporary copper-bronze tones engineered for luxury retail and interior facades",
        unitType: "letter",
        baseRate: 145,
        image: "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/metal/rosegold-1.jpg",
        warranty: {
          pvdCoating: "10-Year PVD Color Retention Guarantee",
          steel: "Lifetime Rust-Proof Grade 304 Certification",
        },
        specs: [
          { label: "Alloy", value: "Grade 304 Austenitic Stainless Steel" },
          { label: "PVD Shade", value: "Rose Gold / Antique Architectural Champagne Bronze" },
          { label: "Assembly", value: "Seamless Micro-TIG Laser Welded Rim Borders" },
        ],
        materialGrades: [
          { id: "rose-gold-hairline", name: "Rose Gold Hairline Satin Metal", multiplier: 1.0, desc: "Luxury salons, flagship boutiques, and private clubs" },
          { id: "bronze-antique", name: "Architectural Champagne Bronze", multiplier: 1.15, desc: "High-end corporate boardrooms and museum signage" },
        ],
        lightingOptions: [
          { id: "osram-3000k", name: "Osram IP67 Warm Architectural Halo", surcharge: 220, glowClass: "glow-warm" },
          { id: "non-lit", name: "Non-Lit Solid Rose Gold", surcharge: 0, glowClass: "" },
        ],
      },
      {
        id: "anodized-aluminum",
        name: "Anodized Architectural Aluminum Channel",
        tagline: "Ultra-lightweight, corrosion-immune matte anodized channel letters for large roof installations",
        unitType: "letter",
        baseRate: 85,
        image: "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
        fallbackImage: "./images/metal/alum-1.jpg",
        warranty: {
          anodizing: "15-Year Zero-Chipping Anodized Layer Warranty",
          led: "2-Year Samsung Module Guarantee",
        },
        specs: [
          { label: "Alloy Series", value: "6063-T6 Structural Architectural Aluminum" },
          { label: "Surface Treatment", value: "15-Micron Natural Silver / Matte Black Anodizing" },
          { label: "Weight Advantage", value: "60% Lighter than Steel; ideal for high rooftop trusses" },
        ],
        materialGrades: [
          { id: "alum-natural", name: "Natural Matte Silver Anodized (15 Micron)", multiplier: 1.0, desc: "Industrial IT parks and high-elevation building tops" },
          { id: "alum-black", name: "Matte Architectural Black Anodized", multiplier: 1.1, desc: "Modern black-accent industrial warehouse facades" },
        ],
        lightingOptions: [
          { id: "samsung-6500k", name: "Samsung IP67 High-Output 6500K", surcharge: 170, glowClass: "glow-frontlit" },
          { id: "non-lit", name: "Non-Lit Lightweight Metal Channel", surcharge: 0, glowClass: "" },
        ],
      },
    ],
  },
};

// ============================================================================
// COLOR SWATCH PALETTES
// ============================================================================
const COLOR_SWATCHES = [
  { id: "pure-white", name: "Pure Day White", hex: "#ffffff", border: "#e2e8f0", textHex: "#0f172a" },
  { id: "translucent-red", name: "Translucent Signal Red", hex: "#dc2626", border: "#b91c1c", textHex: "#ffffff" },
  { id: "cobalt-blue", name: "Cobalt Corporate Blue", hex: "#2563eb", border: "#1d4ed8", textHex: "#ffffff" },
  { id: "safety-yellow", name: "Safety Radium Yellow", hex: "#eab308", border: "#ca8a04", textHex: "#0f172a" },
  { id: "titanium-gold", name: "Titanium Gold Mirror", hex: "#d4af37", border: "#b89628", textHex: "#0f172a" },
  { id: "rose-gold", name: "Rose Gold Brushed", hex: "#b76e79", border: "#9f5b66", textHex: "#ffffff" },
  { id: "hairline-silver", name: "Brushed Silver Hairline", hex: "#94a3b8", border: "#64748b", textHex: "#0f172a" },
  { id: "opaque-black", name: "High-Gloss Jet Black", hex: "#0f172a", border: "#334155", textHex: "#ffffff" },
];

// ============================================================================
// REACTIVE ESTIMATION STATE & WORKSHOP LIVE RATES
// ============================================================================
const state = {
  activeCategory: "acrylic-3d",
  activeProductId: "frontlit-acrylic",
  selectedMaterialId: "cast-3mm",
  selectedColorId: "pure-white",
  selectedLightingId: "samsung-6500k",
  selectedFacadeWall: "facade-granite",
  previewText: "APEX SIGNAGE",

  // Dimensions
  widthFt: 10,
  widthIn: 0,
  heightFt: 3,
  heightIn: 0,
  letterHeightIn: 12,
  letterCount: 11,

  // Workshop Admin Master Rates in INR (₹)
  rates: JSON.parse(localStorage.getItem("apex_sign_rates")) || {
    baseSqftRate: 420,
    baseLetterRate: 95,
    ledModuleSurcharge: 160,
    installationRate: 85,
    gstPercent: 18,
  },

  adminUnlocked: false,
};

// ============================================================================
// DOM ELEMENTS REFERENCE
// ============================================================================
const dom = {
  // Navigation
  navWhatsAppBtn: document.getElementById("navWhatsAppBtn"),
  heroCtaConfigure: document.getElementById("heroCtaConfigure"),

  // Tabs & Catalog
  categoryTabsContainer: document.getElementById("categoryTabsContainer"),
  categoryHeading: document.getElementById("categoryHeading"),
  categoryDesc: document.getElementById("categoryDesc"),
  productCardsContainer: document.getElementById("productCardsContainer"),

  // Dynamic Options
  activeProductBadge: document.getElementById("activeProductBadge"),
  activeProductName: document.getElementById("activeProductName"),
  activeProductTagline: document.getElementById("activeProductTagline"),
  materialsContainer: document.getElementById("materialsContainer"),
  colorSwatchesContainer: document.getElementById("colorSwatchesContainer"),
  lightingOptionsContainer: document.getElementById("lightingOptionsContainer"),
  warrantyBadgeSheet: document.getElementById("warrantyBadgeSheet"),
  warrantyBadgeLed: document.getElementById("warrantyBadgeLed"),

  // Dimensions & Type Toggle
  dimensionSqftControls: document.getElementById("dimensionSqftControls"),
  dimensionLetterControls: document.getElementById("dimensionLetterControls"),
  inputWidthFt: document.getElementById("inputWidthFt"),
  inputWidthIn: document.getElementById("inputWidthIn"),
  inputHeightFt: document.getElementById("inputHeightFt"),
  inputHeightIn: document.getElementById("inputHeightIn"),
  inputLetterHeight: document.getElementById("inputLetterHeight"),
  inputLetterCount: document.getElementById("inputLetterCount"),
  inputPreviewText: document.getElementById("inputPreviewText"),
  calculatedDimensionSummary: document.getElementById("calculatedDimensionSummary"),

  // 3D Canvas Simulator
  previewWallCanvas: document.getElementById("previewWallCanvas"),
  previewSignText: document.getElementById("previewSignText"),
  facadeGraniteBtn: document.getElementById("facadeGraniteBtn"),
  facadeConcreteBtn: document.getElementById("facadeConcreteBtn"),
  facadeWoodBtn: document.getElementById("facadeWoodBtn"),
  facadeGlassBtn: document.getElementById("facadeGlassBtn"),
  toggleIlluminationBtn: document.getElementById("toggleIlluminationBtn"),

  // Quotation Invoice Breakdown
  quoteSerialNo: document.getElementById("quoteSerialNo"),
  quoteDate: document.getElementById("quoteDate"),
  quoteProductName: document.getElementById("quoteProductName"),
  quoteMaterialSpecs: document.getElementById("quoteMaterialSpecs"),
  quoteColorShade: document.getElementById("quoteColorShade"),
  quoteLightingSpec: document.getElementById("quoteLightingSpec"),
  quoteDimensions: document.getElementById("quoteDimensions"),
  quoteCostBase: document.getElementById("quoteCostBase"),
  quoteCostLighting: document.getElementById("quoteCostLighting"),
  quoteCostInstall: document.getElementById("quoteCostInstall"),
  quoteSubtotal: document.getElementById("quoteSubtotal"),
  quoteGstAmount: document.getElementById("quoteGstAmount"),
  quoteGrandTotal: document.getElementById("quoteGrandTotal"),

  // Quotation Actions
  shareWhatsAppBtn: document.getElementById("shareWhatsAppBtn"),
  printPdfBtn: document.getElementById("printPdfBtn"),
  floatingWhatsAppBtn: document.getElementById("floatingWhatsAppBtn"),

  // Admin Rate Panel
  adminRatePanel: document.getElementById("adminRatePanel"),
  toggleAdminPanelBtn: document.getElementById("toggleAdminPanelBtn"),
  adminUnlockForm: document.getElementById("adminUnlockForm"),
  adminPinInput: document.getElementById("adminPinInput"),
  unlockAdminBtn: document.getElementById("unlockAdminBtn"),
  adminControlsArea: document.getElementById("adminControlsArea"),
  adminRateSqft: document.getElementById("adminRateSqft"),
  adminRateLetter: document.getElementById("adminRateLetter"),
  adminRateLed: document.getElementById("adminRateLed"),
  adminRateInstall: document.getElementById("adminRateInstall"),
  saveAdminRatesBtn: document.getElementById("saveAdminRatesBtn"),

  // Specs Table & Lead Form
  specsTableBody: document.getElementById("specsTableBody"),
  leadCaptureForm: document.getElementById("leadCaptureForm"),
  toastContainer: document.getElementById("toastContainer"),
};

// ============================================================================
// INITIALIZATION
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  initLucideIcons();
  generateSerialQuoteNo();
  renderCategoryTabs();
  renderProductCards();
  renderDynamicOptions();
  renderColorSwatches();
  bindInputEvents();
  recalculateQuotation();
});

function initLucideIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function generateSerialQuoteNo() {
  const randomSuffix = Math.floor(1000 + Math.random() * 9000);
  const today = new Date();
  const dateStr = today.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  if (dom.quoteSerialNo) dom.quoteSerialNo.textContent = `EST-2026-${randomSuffix}`;
  if (dom.quoteDate) dom.quoteDate.textContent = dateStr;
}

// ============================================================================
// CATEGORY TABS & PRODUCT CARDS RENDERING
// ============================================================================
function renderCategoryTabs() {
  const categories = Object.keys(PRODUCTS);
  dom.categoryTabsContainer.innerHTML = categories
    .map((catKey) => {
      const cat = PRODUCTS[catKey];
      const isActive = catKey === state.activeCategory;
      const activeClass = isActive
        ? "bg-slate-900 text-white font-semibold shadow-sm border-slate-700"
        : "text-slate-600 hover:text-slate-900 hover:bg-slate-100 border-transparent";

      return `
        <button 
          onclick="selectCategory('${catKey}')" 
          class="px-4 py-2.5 rounded-lg text-xs tracking-tight border transition-all duration-150 whitespace-nowrap ${activeClass}">
          ${escapeHtml(cat.categoryName)}
        </button>
      `;
    })
    .join("");
}

window.selectCategory = function (catKey) {
  state.activeCategory = catKey;
  const firstProduct = PRODUCTS[catKey].items[0];
  state.activeProductId = firstProduct.id;
  state.selectedMaterialId = firstProduct.materialGrades[0].id;
  state.selectedLightingId = firstProduct.lightingOptions[0].id;

  renderCategoryTabs();
  renderProductCards();
  renderDynamicOptions();
  recalculateQuotation();
};

function renderProductCards() {
  const currentCategory = PRODUCTS[state.activeCategory];
  dom.categoryHeading.textContent = currentCategory.categoryName;
  dom.categoryDesc.textContent = currentCategory.categoryDescription;

  dom.productCardsContainer.innerHTML = currentCategory.items
    .map((product) => {
      const isSelected = product.id === state.activeProductId;
      const borderClass = isSelected
        ? "border-amber-500 ring-2 ring-amber-500/20 bg-amber-50/20"
        : "border-slate-200 hover:border-slate-300 bg-white";

      return `
        <div 
          onclick="selectProduct('${product.id}')"
          class="group rounded-xl border p-4 transition-all duration-200 cursor-pointer flex flex-col justify-between ${borderClass}">
          <div>
            <div class="h-40 w-full rounded-lg overflow-hidden relative bg-slate-900 mb-3 border border-slate-100">
              <img 
                src="${product.image}" 
                alt="${escapeHtml(product.name)}" 
                onerror="this.src='https://images.unsplash.com/photo-1542744095-291d1f67b221?auto=format&fit=crop&w=800&q=80'"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
              <div class="absolute bottom-2 left-2 bg-slate-900/80 backdrop-blur-sm px-2 py-0.5 rounded text-[10px] font-mono text-emerald-400 border border-slate-700">
                ${product.unitType === "letter" ? "Per Running Inch" : "Per Sq. Ft"}
              </div>
            </div>
            
            <h4 class="text-sm font-bold text-slate-900 group-hover:text-amber-600 transition-colors">
              ${escapeHtml(product.name)}
            </h4>
            <p class="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
              ${escapeHtml(product.tagline)}
            </p>
          </div>

          <div class="pt-3 mt-3 border-t border-slate-100 flex items-center justify-between">
            <span class="text-[11px] font-mono text-slate-600 font-semibold">
              Starting ₹${product.baseRate} / ${product.unitType === "letter" ? "inch" : "sq.ft"}
            </span>
            <span class="text-xs font-semibold ${isSelected ? "text-amber-600" : "text-slate-400 group-hover:text-slate-600"}">
              ${isSelected ? "Configuring ✓" : "Configure →"}
            </span>
          </div>
        </div>
      `;
    })
    .join("");
}

window.selectProduct = function (productId) {
  state.activeProductId = productId;
  const product = getActiveProduct();
  state.selectedMaterialId = product.materialGrades[0].id;
  state.selectedLightingId = product.lightingOptions[0].id;

  renderProductCards();
  renderDynamicOptions();
  recalculateQuotation();
};

function getActiveProduct() {
  const cat = PRODUCTS[state.activeCategory];
  return cat.items.find((i) => i.id === state.activeProductId) || cat.items[0];
}

// ============================================================================
// DYNAMIC MATERIAL, LIGHTING & SWATCH OPTIONS
// ============================================================================
function renderDynamicOptions() {
  const product = getActiveProduct();

  dom.activeProductName.textContent = product.name;
  dom.activeProductTagline.textContent = product.tagline;
  dom.activeProductBadge.textContent = product.unitType === "letter" ? "3D Channel Letter Configurator" : "Architectural Panel & Signboard Configurator";

  // Toggle between Sq.Ft and Letter count dimension panels
  if (product.unitType === "letter") {
    dom.dimensionSqftControls.classList.add("hidden");
    dom.dimensionLetterControls.classList.remove("hidden");
  } else {
    dom.dimensionSqftControls.classList.remove("hidden");
    dom.dimensionLetterControls.classList.add("hidden");
  }

  // Warranty badges
  dom.warrantyBadgeSheet.textContent = product.warranty.sheet || "5-Year Colorfast Material Warranty";
  dom.warrantyBadgeLed.textContent = product.warranty.led || "2-Year Full IP67 Replacement";

  // Materials & Grades
  dom.materialsContainer.innerHTML = product.materialGrades
    .map((mat) => {
      const isSelected = mat.id === state.selectedMaterialId;
      const borderClass = isSelected
        ? "border-amber-500 bg-amber-50/30 text-amber-950 font-medium"
        : "border-slate-200 bg-white text-slate-700 hover:border-slate-300";

      return `
        <label 
          onclick="selectMaterial('${mat.id}')"
          class="rounded-lg border p-3 cursor-pointer transition-all flex items-start justify-between ${borderClass}">
          <div class="space-y-0.5">
            <div class="text-xs font-bold text-slate-900">${escapeHtml(mat.name)}</div>
            <div class="text-[11px] text-slate-500">${escapeHtml(mat.desc)}</div>
          </div>
          <span class="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
            ${mat.multiplier === 1.0 ? "Base Grade" : `+${Math.round((mat.multiplier - 1) * 100)}% Premium`}
          </span>
        </label>
      `;
    })
    .join("");

  // Lighting Options
  dom.lightingOptionsContainer.innerHTML = product.lightingOptions
    .map((light) => {
      const isSelected = light.id === state.selectedLightingId;
      const borderClass = isSelected
        ? "border-amber-500 bg-amber-50/30 text-amber-950 font-medium"
        : "border-slate-200 bg-white text-slate-700 hover:border-slate-300";

      return `
        <label 
          onclick="selectLighting('${light.id}')"
          class="rounded-lg border p-3 cursor-pointer transition-all flex items-center justify-between ${borderClass}">
          <div class="flex items-center space-x-2">
            <span class="h-2.5 w-2.5 rounded-full ${light.id.includes("warm") ? "bg-amber-400" : (light.id === "non-lit" ? "bg-slate-400" : "bg-sky-400")}"></span>
            <span class="text-xs font-semibold text-slate-800">${escapeHtml(light.name)}</span>
          </div>
          <span class="text-[11px] font-mono text-slate-600 font-semibold">
            ${light.surcharge === 0 ? "Non-Lit" : `+₹${light.surcharge} / ${product.unitType === "letter" ? "letter" : "sq.ft"}`}
          </span>
        </label>
      `;
    })
    .join("");

  // Technical Specs Table
  dom.specsTableBody.innerHTML = product.specs
    .map(
      (spec) => `
      <tr class="border-b border-slate-100 last:border-0 hover:bg-slate-50/60 transition-colors">
        <td class="py-2.5 px-3 font-semibold text-slate-800 font-mono text-[11px] w-2/5">${escapeHtml(spec.label)}</td>
        <td class="py-2.5 px-3 text-slate-600 text-xs">${escapeHtml(spec.value)}</td>
      </tr>
    `
    )
    .join("");
}

window.selectMaterial = function (matId) {
  state.selectedMaterialId = matId;
  renderDynamicOptions();
  recalculateQuotation();
};

window.selectLighting = function (lightId) {
  state.selectedLightingId = lightId;
  renderDynamicOptions();
  recalculateQuotation();
  update3DPreviewVisualizer();
};

function renderColorSwatches() {
  dom.colorSwatchesContainer.innerHTML = COLOR_SWATCHES.map((swatch) => {
    const isSelected = swatch.id === state.selectedColorId;
    const ringClass = isSelected ? "ring-2 ring-amber-500 ring-offset-2 scale-110" : "hover:scale-105";

    return `
      <button 
        onclick="selectColorSwatch('${swatch.id}')" 
        title="${escapeHtml(swatch.name)}"
        class="swatch-item h-8 w-8 rounded-full border shadow-sm transition-all relative ${ringClass}"
        style="background-color: ${swatch.hex}; border-color: ${swatch.border};">
        ${isSelected ? '<span class="absolute inset-0 flex items-center justify-center text-xs font-bold text-slate-700">✓</span>' : ""}
      </button>
    `;
  }).join("");
}

window.selectColorSwatch = function (swatchId) {
  state.selectedColorId = swatchId;
  renderColorSwatches();
  recalculateQuotation();
  update3DPreviewVisualizer();
};

// ============================================================================
// 3D LETTERS CANVAS SIMULATOR & FACADE TEXTURE
// ============================================================================
function update3DPreviewVisualizer() {
  const color = COLOR_SWATCHES.find((c) => c.id === state.selectedColorId) || COLOR_SWATCHES[0];
  const product = getActiveProduct();
  const light = product.lightingOptions.find((l) => l.id === state.selectedLightingId) || product.lightingOptions[0];

  dom.previewSignText.textContent = state.previewText || "APEX SIGNAGE";
  dom.previewSignText.style.color = color.hex;

  // Apply lighting glow
  dom.previewSignText.className = "text-3xl sm:text-5xl tracking-wider font-extrabold transition-all duration-300 letter-3d-bevel ";
  if (light.id !== "non-lit") {
    dom.previewSignText.classList.add(light.glowClass || "glow-frontlit");
  }
}

// Facade Texture switches
[
  { btn: dom.facadeGraniteBtn, class: "facade-granite" },
  { btn: dom.facadeConcreteBtn, class: "facade-concrete" },
  { btn: dom.facadeWoodBtn, class: "facade-wood" },
  { btn: dom.facadeGlassBtn, class: "facade-glass" },
].forEach((item) => {
  if (item.btn) {
    item.btn.addEventListener("click", () => {
      dom.previewWallCanvas.className = `w-full h-56 rounded-xl p-6 flex items-center justify-center relative overflow-hidden transition-all duration-300 ${item.class}`;
      document.querySelectorAll(".facade-btn").forEach((b) => b.classList.remove("ring-2", "ring-amber-400"));
      item.btn.classList.add("ring-2", "ring-amber-400");
    });
  }
});

if (dom.toggleIlluminationBtn) {
  dom.toggleIlluminationBtn.addEventListener("click", () => {
    dom.previewSignText.classList.toggle("glow-frontlit");
    dom.previewSignText.classList.toggle("opacity-40");
    showToast("Illumination toggled", "info");
  });
}

// ============================================================================
// INPUT EVENT BINDINGS & CALCULATION ENGINE
// ============================================================================
function bindInputEvents() {
  // Sq.ft inputs
  [dom.inputWidthFt, dom.inputWidthIn, dom.inputHeightFt, dom.inputHeightIn].forEach((input) => {
    if (input) {
      input.addEventListener("input", () => {
        state.widthFt = Number(dom.inputWidthFt.value) || 0;
        state.widthIn = Number(dom.inputWidthIn.value) || 0;
        state.heightFt = Number(dom.inputHeightFt.value) || 0;
        state.heightIn = Number(dom.inputHeightIn.value) || 0;
        recalculateQuotation();
      });
    }
  });

  // Letter inputs
  if (dom.inputLetterHeight) {
    dom.inputLetterHeight.addEventListener("input", (e) => {
      state.letterHeightIn = Number(e.target.value) || 12;
      recalculateQuotation();
    });
  }

  if (dom.inputLetterCount) {
    dom.inputLetterCount.addEventListener("input", (e) => {
      state.letterCount = Number(e.target.value) || 1;
      recalculateQuotation();
    });
  }

  if (dom.inputPreviewText) {
    dom.inputPreviewText.addEventListener("input", (e) => {
      const text = e.target.value.trim().toUpperCase() || "APEX SIGNAGE";
      state.previewText = text;
      state.letterCount = text.replace(/\s+/g, "").length || 1;
      if (dom.inputLetterCount) dom.inputLetterCount.value = state.letterCount;
      update3DPreviewVisualizer();
      recalculateQuotation();
    });
  }

  // Quote CTA buttons
  if (dom.shareWhatsAppBtn) dom.shareWhatsAppBtn.addEventListener("click", () => shareQuotationWhatsApp());
  if (dom.printPdfBtn) dom.printPdfBtn.addEventListener("click", () => printQuotationInvoice());
  if (dom.floatingWhatsAppBtn) dom.floatingWhatsAppBtn.addEventListener("click", () => shareQuotationWhatsApp());
  if (dom.navWhatsAppBtn) dom.navWhatsAppBtn.addEventListener("click", () => shareQuotationWhatsApp());

  // Hero CTA scroll
  if (dom.heroCtaConfigure) {
    dom.heroCtaConfigure.addEventListener("click", () => {
      document.getElementById("builder-section").scrollIntoView({ behavior: "smooth" });
    });
  }

  // Admin Rate Panel toggle & unlock
  if (dom.toggleAdminPanelBtn) {
    dom.toggleAdminPanelBtn.addEventListener("click", () => {
      dom.adminRatePanel.classList.toggle("hidden");
    });
  }

  if (dom.unlockAdminBtn) {
    dom.unlockAdminBtn.addEventListener("click", () => {
      const pin = dom.adminPinInput.value.trim();
      if (pin === "1234") {
        state.adminUnlocked = true;
        dom.adminUnlockForm.classList.add("hidden");
        dom.adminControlsArea.classList.remove("hidden");
        populateAdminRates();
        showToast("Workshop Admin Panel Unlocked!", "success");
      } else {
        showToast("Incorrect Admin PIN (Default is 1234)", "error");
      }
    });
  }

  if (dom.saveAdminRatesBtn) {
    dom.saveAdminRatesBtn.addEventListener("click", () => {
      state.rates.baseSqftRate = Number(dom.adminRateSqft.value) || 420;
      state.rates.baseLetterRate = Number(dom.adminRateLetter.value) || 95;
      state.rates.ledModuleSurcharge = Number(dom.adminRateLed.value) || 160;
      state.rates.installationRate = Number(dom.adminRateInstall.value) || 85;

      localStorage.setItem("apex_sign_rates", JSON.stringify(state.rates));
      showToast("Live Workshop Rates Updated & Saved!", "success");
      recalculateQuotation();
    });
  }

  // Fast consultation lead form
  if (dom.leadCaptureForm) {
    dom.leadCaptureForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = document.getElementById("leadName").value;
      const phone = document.getElementById("leadPhone").value;
      const city = document.getElementById("leadCity").value;
      const product = getActiveProduct().name;
      const msg = `Hello ApexSign team, I requested an architectural consultation: Name: ${name}, Phone: ${phone}, City: ${city}, Board Type: ${product}.`;
      window.open(`https://wa.me/919876543210?text=${encodeURIComponent(msg)}`, "_blank");
      showToast("Consultation request submitted!", "success");
      dom.leadCaptureForm.reset();
    });
  }
}

function populateAdminRates() {
  dom.adminRateSqft.value = state.rates.baseSqftRate;
  dom.adminRateLetter.value = state.rates.baseLetterRate;
  dom.adminRateLed.value = state.rates.ledModuleSurcharge;
  dom.adminRateInstall.value = state.rates.installationRate;
}

// ============================================================================
// QUOTATION CALCULATION ENGINE (Deterministic Pricing Logic)
// ============================================================================
function recalculateQuotation() {
  const product = getActiveProduct();
  const material = product.materialGrades.find((m) => m.id === state.selectedMaterialId) || product.materialGrades[0];
  const lighting = product.lightingOptions.find((l) => l.id === state.selectedLightingId) || product.lightingOptions[0];
  const color = COLOR_SWATCHES.find((c) => c.id === state.selectedColorId) || COLOR_SWATCHES[0];

  let dimensionStr = "";
  let baseCost = 0;
  let lightingCost = 0;
  let installCost = 0;

  if (product.unitType === "sqft") {
    const totalWidthFt = state.widthFt + state.widthIn / 12;
    const totalHeightFt = state.heightFt + state.heightIn / 12;
    const sqft = Math.max(1, totalWidthFt * totalHeightFt);

    dimensionStr = `${state.widthFt} ft ${state.widthIn} in (W) × ${state.heightFt} ft ${state.heightIn} in (H) = ${sqft.toFixed(2)} Sq.Ft`;
    if (dom.calculatedDimensionSummary) dom.calculatedDimensionSummary.textContent = `${sqft.toFixed(2)} Sq.Ft Total Area`;

    baseCost = sqft * state.rates.baseSqftRate * material.multiplier;
    lightingCost = sqft * lighting.surcharge;
    installCost = sqft * state.rates.installationRate;
  } else {
    // 3D Letter Unit
    const runningInches = state.letterHeightIn * state.letterCount;
    dimensionStr = `${state.letterCount} Letters × ${state.letterHeightIn}" Height = ${runningInches} Total Running Inches`;
    if (dom.calculatedDimensionSummary) dom.calculatedDimensionSummary.textContent = `${runningInches} Running Inches (${state.letterCount} Letters)`;

    baseCost = runningInches * state.rates.baseLetterRate * material.multiplier;
    lightingCost = state.letterCount * lighting.surcharge;
    installCost = state.letterCount * state.rates.installationRate * 1.5;
  }

  const subtotal = Math.round(baseCost + lightingCost + installCost);
  const gstAmount = Math.round(subtotal * (state.rates.gstPercent / 100));
  const grandTotal = subtotal + gstAmount;

  // Update Quotation UI
  dom.quoteProductName.textContent = product.name;
  dom.quoteMaterialSpecs.textContent = `${material.name} (Substrate Multiplier: ${material.multiplier}x)`;
  dom.quoteColorShade.textContent = `${color.name} (${color.hex})`;
  dom.quoteLightingSpec.textContent = lighting.name;
  dom.quoteDimensions.textContent = dimensionStr;

  dom.quoteCostBase.textContent = `₹${Math.round(baseCost).toLocaleString("en-IN")}`;
  dom.quoteCostLighting.textContent = `₹${Math.round(lightingCost).toLocaleString("en-IN")}`;
  dom.quoteCostInstall.textContent = `₹${Math.round(installCost).toLocaleString("en-IN")}`;
  dom.quoteSubtotal.textContent = `₹${subtotal.toLocaleString("en-IN")}`;
  dom.quoteGstAmount.textContent = `₹${gstAmount.toLocaleString("en-IN")}`;
  dom.quoteGrandTotal.textContent = `₹${grandTotal.toLocaleString("en-IN")}`;

  // Store active estimate for export
  state.currentEstimate = {
    productName: product.name,
    materialName: material.name,
    colorName: color.name,
    lightingName: lighting.name,
    dimensions: dimensionStr,
    subtotal,
    gstAmount,
    grandTotal,
  };
}

// ============================================================================
// WHATSAPP QUOTATION SHARE & PRINT PDF
// ============================================================================
function shareQuotationWhatsApp() {
  const est = state.currentEstimate;
  if (!est) return;

  const msg = 
`*APEXSIGN INDUSTRIAL & ARCHITECTURAL QUOTATION*
📄 *Estimate Ref:* ${dom.quoteSerialNo ? dom.quoteSerialNo.textContent : "EST-2026-ONLINE"}
📅 *Date:* ${dom.quoteDate ? dom.quoteDate.textContent : new Date().toLocaleDateString()}
------------------------------------
🏷️ *Product:* ${est.productName}
📐 *Dimensions:* ${est.dimensions}
🧱 *Material Grade:* ${est.materialName}
🎨 *Shade:* ${est.colorName}
💡 *Lighting:* ${est.lightingName}
------------------------------------
💰 *Subtotal:* ₹${est.subtotal.toLocaleString("en-IN")}
🏛️ *GST (18%):* ₹${est.gstAmount.toLocaleString("en-IN")}
⭐ *Grand Total:* ₹${est.grandTotal.toLocaleString("en-IN")}
------------------------------------
🛡️ *Warranty:* 5-Year UV Sheet Colorfast + 2-Year Samsung LED Replacement.
Please arrange an engineer site visit / formal PO generation.`;

  const waUrl = `https://wa.me/919876543210?text=${encodeURIComponent(msg)}`;
  window.open(waUrl, "_blank");
  showToast("Quotation loaded into WhatsApp!", "success");
}

function printQuotationInvoice() {
  showToast("Preparing printable architectural quotation...", "info");
  window.print();
}

// ============================================================================
// TOAST NOTIFICATIONS & UTILITIES
// ============================================================================
function showToast(message, type = "info") {
  if (!dom.toastContainer) return;
  const toast = document.createElement("div");
  toast.className = "flex items-center space-x-2 px-4 py-2.5 rounded-lg border text-xs shadow-xl backdrop-blur-md ";

  if (type === "success") {
    toast.className += "bg-emerald-950/90 border-emerald-500/40 text-emerald-200";
    toast.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 text-emerald-400"></i><span>${escapeHtml(message)}</span>`;
  } else if (type === "error") {
    toast.className += "bg-rose-950/90 border-rose-500/40 text-rose-200";
    toast.innerHTML = `<i data-lucide="alert-octagon" class="w-4 h-4 text-rose-400"></i><span>${escapeHtml(message)}</span>`;
  } else {
    toast.className += "bg-slate-900/90 border-slate-700 text-slate-200";
    toast.innerHTML = `<i data-lucide="info" class="w-4 h-4 text-amber-400"></i><span>${escapeHtml(message)}</span>`;
  }

  dom.toastContainer.appendChild(toast);
  initLucideIcons();

  setTimeout(() => {
    toast.classList.add("opacity-0", "transition-opacity", "duration-300");
    setTimeout(() => toast.remove(), 350);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
