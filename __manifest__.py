{
    "name": "External IDs Management",
    "version": "18.0.1.0.0",
    "category": "Technical",
    "summary": "Manage multiple external system IDs for employees and partners",
    "description": """
        This module allows you to:
        - Define external systems (Discord, RepairShopr, Grafana, Shopify, etc.)
        - Assign multiple external IDs to employees and partners/customers
        - Manage external systems from the UI
        - Track synchronization status
    """,
    "depends": ["hr", "base", "product"],
    "data": [
        "security/ir.model.access.csv",
        "views/external_system_views.xml",
        "views/external_id_views.xml",
        "views/hr_employee_views.xml",
        "views/res_partner_views.xml",
        "views/product_product_views.xml",
        "views/menu_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
