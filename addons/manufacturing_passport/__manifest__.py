{
    "name": "Manufacturing Passport & QC Inspection",
    "version": "18.0.3.0.0",
    "category": "Manufacturing",
    "summary": "Product passport and quality control inspection for manufacturing orders",
    "description": """
        Adds QC Inspection workflow and Product Passport generation
        to Manufacturing Orders. Designed for defense/miltech manufacturers.
    """,
    "author": "Your Name",
    "website": "",
    "license": "LGPL-3",
    "depends": ["mrp", "stock", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sequence_data.xml",
        "views/qc_template_views.xml",
        "views/qc_inspection_views.xml",
        "views/product_passport_views.xml",
        "views/mrp_production_views.xml",
        "reports/inspection_report.xml",
        "reports/passport_report.xml",
        "views/menu.xml",
    ],
    "demo": [
        "demo/demo_data.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
