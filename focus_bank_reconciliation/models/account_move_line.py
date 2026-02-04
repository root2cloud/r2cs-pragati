# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    # =========================================================
    # BRS FIELDS
    # =========================================================
    is_brs_cleared = fields.Boolean(string='BRS Cleared?', default=False, copy=False)
    brs_clearance_date = fields.Date(string='Clearance Date')
    narration = fields.Char(related='move_id.payment_narration', store=True, string='Narration',
                            readonly=True)
    cheque_number = fields.Char(related='move_id.cheque_number', store=True, string='Cheque Number', readonly=True)
    brs_document_type = fields.Char(string="Document Type", compute='_compute_brs_document_type')
    brs_counterpart_account = fields.Char(string="Counterpart Account", compute='_compute_brs_counterpart_account')
    brs_reconciled_str = fields.Char(string="Reconciled", compute='_compute_brs_reconciled_str')
    brs_serial_no = fields.Integer(string='#')
    # =========================================================
    # 1. WRITE OVERRIDE
    # =========================================================
    def write(self, vals):
        """
        Intercepts write calls for BRS fields on Posted entries.
        """
        brs_fields = {'brs_clearance_date', 'is_brs_cleared'}

        if set(vals.keys()).issubset(brs_fields):
            for rec in self:
                set_clauses = []
                params = []

                if 'brs_clearance_date' in vals:
                    set_clauses.append("brs_clearance_date = %s")
                    params.append(vals['brs_clearance_date'])

                if 'is_brs_cleared' in vals:
                    set_clauses.append("is_brs_cleared = %s")
                    params.append(vals['is_brs_cleared'])

                if set_clauses:
                    params.append(rec.id)
                    sql = f"UPDATE account_move_line SET {', '.join(set_clauses)} WHERE id = %s"
                    self.env.cr.execute(sql, tuple(params))

                rec.invalidate_recordset(list(vals.keys()))
            return True

        return super(AccountMoveLine, self).write(vals)

    # =========================================================
    # 2. BUTTON ACTIONS
    # =========================================================
    def action_brs_clear_item(self):
        today = fields.Date.context_today(self)
        for line in self:
            self.env.cr.execute("UPDATE account_move_line SET is_brs_cleared=true, brs_clearance_date=%s WHERE id=%s",
                                (today, line.id))
            line.invalidate_recordset(['is_brs_cleared', 'brs_clearance_date'])
        return True

    def action_brs_revert_item(self):
        for line in self:
            self.env.cr.execute(
                "UPDATE account_move_line SET is_brs_cleared=false, brs_clearance_date=NULL WHERE id=%s", (line.id,))
            line.invalidate_recordset(['is_brs_cleared', 'brs_clearance_date'])
        return True

    # =========================================================
    # 3. COMPUTES
    # =========================================================
    @api.depends('debit', 'credit')
    def _compute_brs_document_type(self):
        for rec in self:
            if rec.debit > 0:
                rec.brs_document_type = 'Bank Receipts'
            elif rec.credit > 0:
                rec.brs_document_type = 'Bank Payments'
            else:
                rec.brs_document_type = ''


    @api.depends('move_id')
    def _compute_brs_counterpart_account(self):
        for line in self:
            # Find all OTHER lines in the same Journal Entry to see where the money went/came from
            other_lines = line.move_id.line_ids.filtered(lambda l: l.id != line.id)

            # Get the names of the accounts from those other lines (e.g. "Sales", "Rent")
            # We use set() to remove duplicates if there are multiple lines
            account_names = list(set(other_lines.mapped('account_id.name')))

            # Join them with commas
            line.brs_counterpart_account = ", ".join(account_names) if account_names else ""

    @api.depends('is_brs_cleared')
    def _compute_brs_reconciled_str(self):
        for rec in self:
            rec.brs_reconciled_str = str(rec.is_brs_cleared)