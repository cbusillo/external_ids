from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestExternalSystem(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ExternalSystem = self.env["external.system"]

    def test_create_external_system(self):
        """Test creating an external system"""
        system = self.ExternalSystem.create(
            {
                "name": "Test System",
                "code": "test_system",
                "description": "Test external system",
                "url": "https://test.example.com",
                "id_format": r"^[A-Z0-9]+$",
                "id_prefix": "TEST-",
            }
        )

        self.assertEqual(system.name, "Test System")
        self.assertEqual(system.code, "test_system")
        self.assertTrue(system.active)

    def test_unique_code_constraint(self):
        """Test that system codes must be unique"""
        self.ExternalSystem.create(
            {
                "name": "System 1",
                "code": "unique_code",
            }
        )

        with self.assertRaises(ValidationError):
            self.ExternalSystem.create(
                {
                    "name": "System 2",
                    "code": "unique_code",
                }
            )

    def test_unique_name_constraint(self):
        """Test that system names must be unique"""
        self.ExternalSystem.create(
            {
                "name": "Unique Name",
                "code": "code1",
            }
        )

        with self.assertRaises(ValidationError):
            self.ExternalSystem.create(
                {
                    "name": "Unique Name",
                    "code": "code2",
                }
            )

    def test_external_id_count(self):
        """Test the external_id_count computed field"""
        system = self.ExternalSystem.create(
            {
                "name": "Count Test System",
                "code": "count_test",
            }
        )

        self.assertEqual(system.external_id_count, 0)

        # Create an external ID linked to this system
        partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.env["external.id"].create(
            {
                "res_model": "res.partner",
                "res_id": partner.id,
                "system_id": system.id,
                "external_id": "PARTNER123",
            }
        )

        system._compute_external_id_count()
        self.assertEqual(system.external_id_count, 1)

    def test_archive_system(self):
        """Test archiving an external system"""
        system = self.ExternalSystem.create(
            {
                "name": "Archive Test",
                "code": "archive_test",
            }
        )

        self.assertTrue(system.active)
        system.active = False
        self.assertFalse(system.active)

        # Archived systems should not appear in active domain
        active_systems = self.ExternalSystem.search([("active", "=", True)])
        self.assertNotIn(system, active_systems)
