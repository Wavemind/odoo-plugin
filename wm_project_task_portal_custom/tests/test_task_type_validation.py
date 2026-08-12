from odoo.tests.common import TransactionCase


class TestTaskTypeValidation(TransactionCase):
    """Tests for the is_awaiting_validation flag on project.task.type (Story 1.2)."""

    def test_default_is_false(self):
        """is_awaiting_validation defaults to False on new stages."""
        stage = self.env['project.task.type'].create({'name': 'Test Stage WM'})
        self.assertFalse(stage.is_awaiting_validation)

    def test_can_set_true(self):
        """is_awaiting_validation can be set to True."""
        stage = self.env['project.task.type'].create({
            'name': 'En attente validation client',
            'is_awaiting_validation': True,
        })
        self.assertTrue(stage.is_awaiting_validation)

    def test_portal_can_read_stage(self):
        """Portal user can read project.task.type including is_awaiting_validation.

        Required for portal controllers that check stage.is_awaiting_validation
        without sudo() — as per ARCH4 defense-in-depth pattern.
        """
        stage = self.env['project.task.type'].create({
            'name': 'Stage Portail Test WM',
            'is_awaiting_validation': True,
        })
        portal_user = self.env['res.users'].search(
            [('groups_id', 'in', self.env.ref('base.group_portal').id)],
            limit=1,
        )
        if not portal_user:
            self.skipTest("No portal user available in test database")

        stage_as_portal = stage.with_user(portal_user)
        self.assertTrue(stage_as_portal.is_awaiting_validation)
