{
    "name": "External IDs Management",
    "version": "18.0.1.0.1",
    "category": "Technical",
    "summary": "Manage multiple external system IDs for employees, partners, and products.",
    "description": """
        This module allows you to:
        - Define external systems (Discord, RepairShopr, Grafana, Shopify, etc.)
        - Assign and manage multiple external IDs per record (employees, partners, products)
        - Track synchronization status and quickly access linked records

        Designed to be compatible with OCA conventions (README, i18n, conservative access rights).
    """,
    "author": "Chris Busillo (Shiny Computers)",
    "maintainers": ["cbusillo"],
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": ["hr", "base", "product"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir.rule.xml",
        "views/external_system_views.xml",
        "views/external_id_views.xml",
        "views/hr_employee_views.xml",
        "views/res_partner_views.xml",
        "views/product_product_views.xml",
        "views/menu_views.xml",
    ],
    "images": ["static/description/icon.png"],
    "installable": True,
    "application": False,
}
