from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class InternalTransactions(models.Model):
    _name = 'internal.transaction'
    _description = 'Internal Transaction'

    # Fields
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, tracking=True,
                       default=lambda self: _('New'))
    date = fields.Date(string="Date", required=True)
    boole = fields.Selection([('send', 'Send'), ('receive', 'Receive')], string="Payment Type", default='send')
    source_acc = fields.Many2one('account.account', string="From Account", domain=[('account_type', '=', 'asset_cash')])
    dest_acc = fields.Many2one('account.account', string="To Account", domain=[('account_type', '=', 'asset_cash')])
    amount = fields.Float(string="Amount", required=True)
    # invoiced_amount = fields.Float(string="Reconciled Amount")
    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        readonly=1,
        default=lambda self: self._default_journal_id()
    )
    is_complete_trans = fields.Boolean(string='Complete Transaction', default=False)
    transaction_id = fields.Many2one('account.bank.statement.line', string='Trans ID')
    remarks = fields.Text(string='Remarks')
    journal_entries = fields.Integer(string='Journal Entries', compute='_compute_journal_count')
    # Field to link the journal entry
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    reconciled_amount = fields.Float(string="Reconciled Amount", store=True)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submit'), ('approve', 'Approved'), ('post', 'Posted'),
                              ('cancel', 'Cancelled')], default='draft')

    department_id = fields.Many2one('hr.department', 'Department', tracking=True, required=True)
    approval_level_1 = fields.Many2one('res.users', string='Approver Level 1', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_2 = fields.Many2one('res.users', string='Approver Level 2', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_level_3 = fields.Many2one('res.users', string='Approver Level 3', domain="[('share', '=', False)]",
                                       readonly=True)
    approval_id = fields.Many2one('approval.request', string='Approval ID')

    request_owner_id = fields.Many2one('res.users', string="Request Owner",
                                       check_company=True, domain="[('company_ids', 'in', company_id)]",
                                       default=lambda self: self.env.user)

    approve_status = fields.Selection([('pending', 'Pending'), ('approve', 'Approved')],
                                      string='Approval Status', default='pending')

    is_approval_user = fields.Boolean('res.users', compute="_compute_is_approval_user")

    @api.depends('approval_level_1', 'approval_level_2', 'approval_level_3', 'state')
    def _compute_is_approval_user(self):
        for rec in self:
            user_id = self.env.user.id
            rec.is_approval_user = False
            if rec.state in ['submit', 'waiting2', 'waiting3']:
                if rec.state == 'submit' and rec.approval_level_1 and rec.approval_level_1.id == user_id:
                    rec.is_approval_user = True
                elif rec.state == 'waiting2' and rec.approval_level_2 and rec.approval_level_2.id == user_id:
                    rec.is_approval_user = True
                elif rec.state == 'waiting3' and rec.approval_level_3 and rec.approval_level_3.id == user_id:
                    rec.is_approval_user = True

    @api.onchange('department_id')
    def _onchange_department_id(self):
        if self.department_id:
            self.approval_level_1 = self.department_id.approver1.id if self.department_id.approver1 else False
            self.approval_level_2 = self.department_id.approver2.id if self.department_id.approver2 else False
            self.approval_level_3 = self.department_id.approver3.id if self.department_id.approver3 else False
        else:
            self.approval_level_1 = False
            self.approval_level_2 = False
            self.approval_level_3 = False

    def approve_contra(self):
        self.write({'state': 'approve'})

    # def _compute_is_approval_user(self):
    #     for lp in self:
    #         approver_list = []
    #
    #         if lp.approval_level_1:
    #             approver_list.append(lp.approval_level_1.id)
    #         if lp.approval_level_2:
    #             approver_list.append(lp.approval_level_2.id)
    #         if lp.approval_level_3:
    #             approver_list.append(lp.approval_level_3.id)
    #         if lp.env.user.id in approver_list:
    #             lp.is_approval_user = True
    #         else:
    #             lp.is_approval_user = False

    def send_for_approval(self):
        self.write({'state': 'submit'})
        approver_list = []

        if self.approval_level_1:
            approver_list.append(self.approval_level_1.id)
        if self.approval_level_2:
            approver_list.append(self.approval_level_2.id)
        if self.approval_level_3:
            approver_list.append(self.approval_level_3.id)
        if not approver_list:
            raise ValidationError(_('Please Assign atleast one approver'))
        return True

    @api.model
    def _default_journal_id(self):
        """Return the ID of the default journal ('Miscellaneous Operations')."""
        journal = self.env['account.journal'].search([
            ('name', '=', 'Miscellaneous Operations')
        ], limit=1)
        return journal.id if journal else None

    def _compute_journal_count(self):
        """Compute the number of journal entries associated with this transaction."""
        for rec in self:
            count = self.env['account.move'].search_count([('internal_trans_id', '=', rec.id)])
            rec.journal_entries = count

    @api.model_create_multi
    def create(self, values_list):
        """Create a draft journal entry when the record is created."""
        records = super(InternalTransactions, self).create(values_list)

        for record in records:
            # Generate sequence if name is 'New'
            if record.name == _('New'):
                if record.boole == 'send':
                    sequence = self.env['ir.sequence'].next_by_code('send.sequence')
                    if sequence:
                        record.name = sequence
                    else:
                        raise UserError(_("Send sequence not found."))

                elif record.boole == 'receive':
                    sequence = self.env['ir.sequence'].next_by_code('receive.sequence')
                    if sequence:
                        record.name = sequence
                    else:
                        raise UserError(_("Receive sequence not found."))

            # Create a draft journal entry
            journal_entry = self.env['account.move'].create({
                'date': record.date,
                'ref': record.name,
                'journal_id': record.journal_id.id,
                'internal_trans_id': record.id,
                'state': 'draft',  # Keep the journal entry in draft state
            })

            # Create journal items
            account_values = []

            if record.boole == 'receive':
                # Debit source account
                account_values.append((0, 0, {
                    'account_id': record.source_acc.id,
                    'debit': record.amount,
                    'credit': 0.0,
                    'date': record.date,
                }))
                # Credit destination account
                account_values.append((0, 0, {
                    'account_id': record.dest_acc.id,
                    'debit': 0.0,
                    'credit': record.amount,
                    'date': record.date,
                }))
            elif record.boole == 'send':
                # Credit source account
                account_values.append((0, 0, {
                    'account_id': record.source_acc.id,
                    'debit': 0.0,
                    'credit': record.amount,
                    'date': record.date,
                }))
                # Debit destination account
                account_values.append((0, 0, {
                    'account_id': record.dest_acc.id,
                    'debit': record.amount,
                    'credit': 0.0,
                    'date': record.date,
                }))

            # Add journal items to the journal entry
            journal_entry.write({
                'line_ids': account_values,
            })

            # Link the journal entry to the internal transaction
            record.journal_entry_id = journal_entry.id

        return records

    def action_confirm(self):
        """Confirm the internal transaction and post the journal entry."""
        self.ensure_one()
        self.state = 'post'
        # Ensure the journal entry is linked to the internal transaction
        if not self.journal_entry_id:
            raise UserError(_("No linked journal entry found for this transaction."))

        # Post the draft journal entry
        self.journal_entry_id.action_post()

        return True

    def action_internal_journal_entries(self):
        """View the journal entries linked to this transaction."""
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'domain': [('internal_trans_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    @api.model
    def _write(self, values):
        """
        Override the write method to update the linked journal entry when data changes.
        """
        # Call the original write method
        result = super(InternalTransactions, self)._write(values)

        # Check which fields have been changed
        fields_changed = set(values.keys())

        # If relevant fields have changed, update the journal entry
        if fields_changed & {'date', 'boole', 'source_acc', 'dest_acc', 'amount'}:
            self.update_journal_entry()

        return result

    def update_journal_entry(self):
        """
        Update the journal entry associated with this internal transaction.
        """
        self.ensure_one()

        # If there is no linked journal entry, skip
        if not self.journal_entry_id:
            return

        # Update the journal entry header fields (date, ref, journal)
        self.journal_entry_id.write({
            'date': self.date,
            'ref': self.name,
            'journal_id': self.journal_id.id,
        })

        # Update the journal entry lines based on the new data
        # **Important:** Get the lines before potentially deleting them
        journal_entry_lines = self.journal_entry_id.line_ids

        # Delete existing lines to avoid duplicates (optional)
        # You might want to comment this out depending on your business logic
        # journal_entry_lines.unlink()

        # Update the debit and credit lines based on boole value
        if self.boole == 'receive':
            debit_account = self.source_acc
            credit_account = self.dest_acc
        else:
            debit_account = self.dest_acc
            credit_account = self.source_acc

        # Create new journal items instead of updating existing
