from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = 'ledger.payment.bill.wise.adjustments'

    department_id = fields.Many2one('hr.department', string="Department")
    approval_level_1 = fields.Many2one('res.users', string='Approval User')

    # Extend states: keep Odoo’s 'draft' & 'posted', add custom
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('waiting', 'Waiting for Approval'),
    #     ('approved', 'Approved'),
    #     ('rejected', 'Rejected')
    # ], string='Status', default='draft', tracking=True)

    @api.onchange('department_id')
    def _onchange_department_id(self):
        """ Auto-assign approver based on department """
        if self.department_id and hasattr(self.department_id, 'approver1'):
            self.approval_level_1 = self.department_id.approver1.id
        else:
            self.approval_level_1 = False

    def action_submit(self):
        for rec in self:
            if not rec.approval_level_1:
                raise ValidationError(_("Please assign an approval user."))
            rec.state = 'waiting'
            rec._create_approval_activity()

    def action_approve(self):
        for rec in self:
            if self.env.user != rec.approval_level_1:
                raise ValidationError(_("Only the assigned approver can approve this payment."))
            rec.state = 'approved'
            rec._remove_approval_activity()

    def action_reject(self):
        for rec in self:
            if self.env.user != rec.approval_level_1:
                raise ValidationError(_("Only the assigned approver can reject this payment."))
            rec.state = 'rejected'
            rec._remove_approval_activity()

    def action_reset_to_draft(self):
        self._remove_approval_activity()
        self.write({'state': 'draft'})

    def _create_approval_activity(self):
        for rec in self:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'res_model_id': self.env['ir.model']._get_id('account.payment'),
                'res_id': rec.id,
                'user_id': rec.approval_level_1.id,
                'summary': f'Payment {rec.name} Approval',
                'note': 'Please approve the submitted Payment.',
                'date_deadline': fields.Date.today()
            })

    def _remove_approval_activity(self):
        self.env['mail.activity'].search([
            ('res_model', '=', 'account.payment'),
            ('res_id', 'in', self.ids)
        ]).unlink()