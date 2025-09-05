from ..common_imports import tagged, UNIT_TAGS
from ..fixtures.base import UnitTestCase


@tagged(*UNIT_TAGS)
class TestExternalIdSecurity(UnitTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Companies
        cls.CompanyA = cls.env["res.company"].create({"name": "Company A"})
        cls.CompanyB = cls.env["res.company"].create({"name": "Company B"})

        # Users with scoped groups
        GroupHR = cls.env.ref("hr.group_hr_user")
        GroupPartnerMgr = cls.env.ref("base.group_partner_manager")
        GroupProductMgr = cls.env.ref("product.group_product_manager")
        GroupUser = cls.env.ref("base.group_user")

        def _mk_user(name: str, company, groups):
            user = (
                cls.env["res.users"]
                .with_context(no_reset_password=True)
                .create(
                    {
                        "name": name,
                        "login": f"{name.lower().replace(' ', '.')}@example.com",
                        "email": f"{name.lower().replace(' ', '.')}@example.com",
                        "company_id": company.id,
                        "company_ids": [(6, 0, [company.id])],
                        "groups_id": [(6, 0, [g.id for g in groups])],
                    }
                )
            )
            return user

        cls.u_hr = _mk_user("HR User", cls.CompanyA, [GroupHR, GroupUser])
        cls.u_partner = _mk_user("Partner Manager", cls.CompanyA, [GroupPartnerMgr, GroupUser])
        cls.u_product = _mk_user("Product Manager", cls.CompanyA, [GroupProductMgr, GroupUser])
        cls.u_basic = _mk_user("Basic User", cls.CompanyA, [GroupUser])

        # Records in companies
        cls.partner_a = (
            cls.env["res.partner"].with_company(cls.CompanyA).create({"name": "Partner A", "company_id": cls.CompanyA.id})
        )
        cls.partner_b = (
            cls.env["res.partner"].with_company(cls.CompanyB).create({"name": "Partner B", "company_id": cls.CompanyB.id})
        )

        cls.product_a = cls.env["product.product"].with_company(cls.CompanyA).create({"name": "Product A"})
        cls.employee_a = (
            cls.env["hr.employee"].with_company(cls.CompanyA).create({"name": "Emp A", "first_name": "Emp", "last_name": "A"})
        )

        cls.system = cls.env["external.system"].create({"name": "Discord", "code": "discord"})

        cls.eid_partner_a = cls.env["external.id"].create(
            {"res_model": "res.partner", "res_id": cls.partner_a.id, "system_id": cls.system.id, "external_id": "P-A"}
        )
        cls.eid_partner_b = cls.env["external.id"].create(
            {"res_model": "res.partner", "res_id": cls.partner_b.id, "system_id": cls.system.id, "external_id": "P-B"}
        )
        cls.eid_product_a = cls.env["external.id"].create(
            {"res_model": "product.product", "res_id": cls.product_a.id, "system_id": cls.system.id, "external_id": "PR-A"}
        )
        cls.eid_employee_a = cls.env["external.id"].create(
            {"res_model": "hr.employee", "res_id": cls.employee_a.id, "system_id": cls.system.id, "external_id": "E-A"}
        )

    def test_basic_user_cannot_read_any_external_ids(self) -> None:
        ExternalId_basic = self.env(user=self.u_basic)["external.id"]
        self.assertFalse(ExternalId_basic.search([], limit=1))

    def test_partner_manager_sees_only_partner_ids_in_company(self) -> None:
        ExternalId_partner = self.env(user=self.u_partner)["external.id"]
        ids = ExternalId_partner.search([])
        models = set(ids.mapped("res_model"))
        self.assertEqual(models, {"res.partner"})
        self.assertIn(self.eid_partner_a, ids)
        self.assertNotIn(self.eid_partner_b, ids)  # other company hidden
        self.assertNotIn(self.eid_employee_a, ids)
        self.assertNotIn(self.eid_product_a, ids)

    def test_product_manager_sees_only_product_ids(self) -> None:
        ExternalId_product = self.env(user=self.u_product)["external.id"]
        ids = ExternalId_product.search([])
        models = set(ids.mapped("res_model"))
        self.assertEqual(models, {"product.product"})
        self.assertIn(self.eid_product_a, ids)
        self.assertNotIn(self.eid_partner_a, ids)
        self.assertNotIn(self.eid_employee_a, ids)

    def test_hr_user_sees_only_employee_ids(self) -> None:
        ExternalId_hr = self.env(user=self.u_hr)["external.id"]
        ids = ExternalId_hr.search([])
        models = set(ids.mapped("res_model"))
        self.assertEqual(models, {"hr.employee"})
        self.assertIn(self.eid_employee_a, ids)
        self.assertNotIn(self.eid_partner_a, ids)
        self.assertNotIn(self.eid_product_a, ids)
