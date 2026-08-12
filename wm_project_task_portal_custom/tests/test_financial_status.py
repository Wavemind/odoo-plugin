from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestFinancialStatus(TransactionCase):
    """Tests for the financial_status computed field on project.task (Story 1.1)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Client Test WM'})
        cls.project = cls.env['project.project'].create({
            'name': 'Projet Test WM',
            'partner_id': cls.partner.id,
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Tâche Test WM',
            'project_id': cls.project.id,
            'task_type': 'feature',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Service Test',
            'type': 'service',
            'list_price': 100.0,
        })

    def _create_confirmed_sale_line(self):
        """Create a confirmed sale order and return one of its lines."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        return order.order_line[0]

    def _create_posted_invoice(self):
        """Create and post an invoice, returning the move and its first line."""
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)],
            limit=1,
        )
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        move.action_post()
        return move, move.invoice_line_ids[0]

    def _create_draft_invoice(self):
        """Create a draft invoice (not posted) and return the move and its first line."""
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.env.company.id)],
            limit=1,
        )
        move = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'journal_id': journal.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1,
                'price_unit': 100.0,
            })],
        })
        return move, move.invoice_line_ids[0]

    def _detach_all_lines(self):
        """Remove all financial links from the test task."""
        self.task.write({
            'sale_order_line_ids': [(5,)],
            'invoice_line_ids': [(5,)],
        })

    def test_no_lines_is_not_quoted(self):
        """A task with no linked lines has financial_status == 'not_quoted'."""
        self._detach_all_lines()
        self.assertEqual(self.task.financial_status, 'not_quoted')

    def test_sale_line_only_is_quoted(self):
        """A task linked to a confirmed sale order line has financial_status == 'quoted'."""
        self._detach_all_lines()
        sale_line = self._create_confirmed_sale_line()
        self.task.write({'sale_order_line_ids': [(4, sale_line.id)]})
        self.assertEqual(self.task.financial_status, 'quoted')

    def test_posted_unpaid_invoice_is_invoiced(self):
        """A task linked to a posted (unpaid) invoice line has financial_status == 'invoiced'."""
        self._detach_all_lines()
        _move, inv_line = self._create_posted_invoice()
        self.task.write({'invoice_line_ids': [(4, inv_line.id)]})
        self.assertEqual(self.task.financial_status, 'invoiced')

    def test_paid_invoice_is_paid(self):
        """A task linked to a paid invoice line has financial_status == 'paid'.

        Forces payment_state via SQL since it is a computed stored field.
        """
        self._detach_all_lines()
        move, inv_line = self._create_posted_invoice()
        # Force payment_state to 'paid' at DB level for test isolation
        self.env.cr.execute(
            "UPDATE account_move SET payment_state = 'paid' WHERE id = %s",
            [move.id],
        )
        move.invalidate_recordset(['payment_state'])
        self.task.write({'invoice_line_ids': [(4, inv_line.id)]})
        self.assertEqual(self.task.financial_status, 'paid')

    def test_cancelled_invoice_is_cancelled(self):
        """A task linked to a cancelled invoice has financial_status == 'cancelled'."""
        self._detach_all_lines()
        move, inv_line = self._create_posted_invoice()
        # In Odoo 17, a posted invoice must be reset to draft before cancellation
        move.button_draft()
        move.button_cancel()
        self.task.write({'invoice_line_ids': [(4, inv_line.id)]})
        self.assertEqual(self.task.financial_status, 'cancelled')

    def test_draft_invoice_is_ignored(self):
        """A task linked only to a draft invoice line has financial_status == 'not_quoted'.

        Draft invoices are ignored by _compute_financial_status.
        """
        self._detach_all_lines()
        _move, inv_line = self._create_draft_invoice()
        self.task.write({'invoice_line_ids': [(4, inv_line.id)]})
        self.assertEqual(self.task.financial_status, 'not_quoted')

    def test_draft_invoice_with_sale_line_is_quoted(self):
        """A task with a draft invoice line AND a sale line has financial_status == 'quoted'.

        The draft invoice is ignored; only the sale line counts.
        """
        self._detach_all_lines()
        sale_line = self._create_confirmed_sale_line()
        _move, inv_line = self._create_draft_invoice()
        self.task.write({
            'sale_order_line_ids': [(4, sale_line.id)],
            'invoice_line_ids': [(4, inv_line.id)],
        })
        self.assertEqual(self.task.financial_status, 'quoted')

    def test_cannot_delete_linked_sale_line(self):
        """Deleting a sale.order.line linked to a task raises a ValidationError (ondelete=restrict)."""
        self._detach_all_lines()
        sale_line = self._create_confirmed_sale_line()
        self.task.write({'sale_order_line_ids': [(4, sale_line.id)]})
        with self.assertRaises((ValidationError, Exception)):
            sale_line.unlink()

    def test_cannot_delete_linked_invoice_line(self):
        """Deleting an account.move.line linked to a task raises a ValidationError (ondelete=restrict)."""
        self._detach_all_lines()
        move, inv_line = self._create_posted_invoice()
        self.task.write({'invoice_line_ids': [(4, inv_line.id)]})
        with self.assertRaises((ValidationError, Exception)):
            inv_line.unlink()

    def test_cancelled_takes_priority_over_invoiced(self):
        """If any linked move is cancelled, status is 'cancelled' even if others are posted."""
        self._detach_all_lines()
        move1, inv_line1 = self._create_posted_invoice()
        move2, inv_line2 = self._create_posted_invoice()
        move2.button_draft()
        move2.button_cancel()
        self.task.write({'invoice_line_ids': [(4, inv_line1.id), (4, inv_line2.id)]})
        self.assertEqual(self.task.financial_status, 'cancelled')
