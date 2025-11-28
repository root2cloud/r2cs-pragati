from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class LedgerPayment(models.Model):
    _name = 'ledger.payment'

    # Define fields
    date = fields.Date(string="Date", default=fields.datetime.now())
    boole = fields.Selection([('send', 'Send'), ('receive', 'Receive')], string="Payment Type", default='send')
    source_acc = fields.Many2one('account.account', string="Customer Account")
    dest_acc = fields.Many2one('account.account', string="To Account")
    amount = fields.Float(string="Amount")
    amount_paid = fields.Float(string="Amount paid")
    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        readonly=0,
        default=lambda self: self._default_journal_id()

    )
    is_complete_trans = fields.Boolean(string='Complete Transaction', default=False)
    transaction_id = fields.Many2one('account.bank.statement.line', string='Trans ID')
    remarks = fields.Text(string='Remarks')
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, tracking=True,
                       default=lambda self: _('New'))
    journal_entries = fields.Integer(string='Journal Entries', compute='_compute_journal_count')
    # Link to the journal entry
    journal_entry_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    bank_manual_line_ids = fields.One2many('bank.account.manual.line', 'ledger_pay_id', string='Bank Manual Line Ids',
                                           store=True, readonly=False)
    account_move_ids = fields.One2many('account.move', 'ledger_pay_id', string='Account Move Ids',
                                       compute='_compute_account_move_ids', store=True, readonly=False)
    reconciled_amount = fields.Float(string='Reconciled Amount', compute='_compute_amount', store=True)
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submit'), ('approve', 'Approved'), ('post', 'Posted'),
                              ('recocile', 'Reconciled'), ('cancel', 'Cancelled')], default='draft')
    ledger_or_bill = fields.Selection([('ledger', 'Ledger'), ('bill', 'Bill')], default='ledger')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)

    def _compute_journal_count(self):
        for rec in self:
            count = self.env['account.move'].search_count([('ledger_payment_id', '=', rec.id)])
            rec.journal_entries = count

    @api.model
    def _default_journal_id(self):
        journal = self.env['account.journal'].search([('name', '=', 'HDFC Bank - 50200023192175')], limit=1)
        return journal.id if journal else None

    # @api.model_create_multi
    # def create(self, values_list):
    #     records = super(LedgerPayment, self).create(values_list)

    #     for record in records:
    #         if record.name == _('New'):
    #             if record.boole == 'send' and record.ledger_or_bill == 'ledger':
    #                 sequence = self.env['ir.sequence'].next_by_code('ledger.payment.ledger')
    #                 if sequence:
    #                     record.name = sequence
    #                 else:
    #                     raise UserError(_("Send sequence not found."))
    #             elif record.boole == 'send' and record.ledger_or_bill == 'bill':
    #                 sequence = self.env['ir.sequence'].next_by_code('ledger.payment.bill')
    #                 if sequence:
    #                     record.name = sequence
    #                 else:
    #                     raise UserError(_("Send sequence not found."))

    #             elif record.boole == 'receive':
    #                 sequence = self.env['ir.sequence'].next_by_code('ledger.payment')
    #                 if sequence:
    #                     record.name = sequence
    #                 else:
    #                     raise UserError(_("Receive sequence not found."))

    #         journal_entry = self.env['account.move'].create({
    #             'date': record.date,
    #             'ref': record.name,
    #             'journal_id': record.journal_id.id,
    #             'ledger_payment_id': record.id,
    #             'state': 'draft',  
    #         })

    #         account_values = []

    #         if record.boole == 'receive':
    #             account_values.append((0, 0, {
    #                 'account_id': record.source_acc.id,
    #                 'debit': record.amount,
    #                 'credit': 0.0,
    #                 'date': record.date,
    #             }))
    #             account_values.append((0, 0, {
    #                 'account_id': record.dest_acc.id,
    #                 'debit': 0.0,
    #                 'credit': record.amount,
    #                 'date': record.date,
    #             }))
    #         elif record.boole == 'send':
    #             account_values.append((0, 0, {
    #                 'account_id': record.source_acc.id,
    #                 'debit': 0.0,
    #                 'credit': record.amount,
    #                 'date': record.date,
    #             }))
    #             account_values.append((0, 0, {
    #                 'account_id': record.dest_acc.id,
    #                 'debit': record.amount,
    #                 'credit': 0.0,
    #                 'date': record.date,
    #             }))

    #         journal_entry.write({
    #             'line_ids': account_values,
    #         })

    #         record.journal_entry_id = journal_entry.id

    #     return records

    @api.model_create_multi
    def create(self, values_list):
        records = super(LedgerPayment, self).create(values_list)

        for record in records:

            if record.name == _('New'):
                if record.boole == 'send' and record.ledger_or_bill == 'ledger':
                    sequence = self.env['ir.sequence'].next_by_code('ledger.payment.ledger')
                    if sequence:
                        record.name = sequence
                        print("pppppppppppppppppp", record.name)
                    else:
                        raise UserError(_("Send sequence not found."))
                elif record.boole == 'send' and record.ledger_or_bill == 'bill':
                    sequence = self.env['ir.sequence'].next_by_code('ledger.payment.bill')
                    if sequence:
                        record.name = sequence
                        print("lllllllllllllllllllll", record.name)
                    else:
                        raise UserError(_("Send sequence not found."))


                elif record.boole == 'receive':
                    sequence = self.env['ir.sequence'].next_by_code('ledger.payment.ledger')
                    if sequence:
                        record.name = sequence
                    else:
                        raise UserError(_("Receive sequence not found."))

            # Create a draft journal entry
            journal_entry = self.env['account.move'].create({
                'date': record.date,
                'ref': record.name,
                'journal_id': record.journal_id.id,
                'ledger_payment_id': record.id,

                'state': 'draft',  # Keep journal entry in draft state
            })

            # Create journal items for the entry
            account_values = []

            # Determine debit and credit amounts
            if record.boole == 'receive':
                # Debit the source account
                account_values.append((0, 0, {
                    'account_id': record.source_acc.id,
                    'debit': record.amount,
                    'credit': 0.0,
                    'date': record.date,
                }))
                # Credit the destination account
                account_values.append((0, 0, {
                    'account_id': record.dest_acc.id,
                    'debit': 0.0,
                    'credit': record.amount,
                    'date': record.date,
                }))
            elif record.boole == 'send':
                # Credit the source account
                account_values.append((0, 0, {
                    'account_id': record.source_acc.id,
                    'debit': 0.0,
                    'credit': record.amount,
                    'date': record.date,
                }))
                # Debit the destination account
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

            # Link the journal entry to the ledger payment
            record.journal_entry_id = journal_entry.id

        return records

    @api.onchange('source_acc')
    def _onchange_source_acc(self):
        """Overrides the onchange method to set account_move_ids to customer invoices only."""

        # Ensure source_acc is set
        if not self.source_acc:
            return

        customer_acc = self.source_acc.id
        print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG", customer_acc)
        res = self.env['res.partner'].search([('property_account_receivable_id.id', '=', customer_acc)])
        print("GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG", res)

        # Get only customer invoices (type='out_invoice')
        customer_invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'paid'),
            ('is_manual_reconcile', '=', False),
            # ('partner_id.property_account_receivable_id','=',self.source_acc.id)
        ], limit=200)

        # Assign the filtered account.move records to the account_move_ids field
        self.account_move_ids = customer_invoices
        self.bank_manual_line_ids = [(5, 0, 0)]
        # Prepare and set bank_manual_line_ids
        bank_manual_values = []
        for invoice in customer_invoices:
            bank_manual_values.append((0, 0, {
                'name': invoice.name,  # Invoice number
                'date': invoice.date,
                'amount': invoice.amount_total_signed,
                'customer_name': invoice.partner_id.name if invoice.partner_id else '',
                'is_manual_reconcile': invoice.is_manual_reconcile,
                'invoice_id': invoice.id,
                'provider_reference': invoice.transaction_ids and invoice.transaction_ids[
                    0].provider_reference or False,
                'manual_reconcile_amount': invoice.manual_reconcile_amount,
            }))

        # Assign the list of dictionaries as records to bank_manual_line_ids
        self.bank_manual_line_ids = bank_manual_values

    def action_confirm(self):
        """Confirm the internal transaction and post the draft journal entry."""
        self.ensure_one()

        # Check if there is a linked journal entry
        if not self.journal_entry_id:
            raise UserError(_("No linked journal entry found for this transaction."))

        # Post the journal entry
        self.journal_entry_id.action_post()

        # Mark the transaction as complete
        self.is_complete_trans = True
        self.state = 'post'

        return True

    def action_internal_journal_entries(self):
        return {
            'name': _('Journal Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'domain': [('ledger_payment_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current',
        }

    @api.model
    def _write(self, values):
        """
        Override the write method to update the linked journal entry when data changes.
        """
        # Call the original write method
        result = super(LedgerPayment, self)._write(values)

        # Check which fields have been changed
        fields_changed = set(values.keys())

        # If relevant fields have changed, update the journal entry
        if fields_changed & {'date', 'boole', 'source_acc', 'dest_acc', 'amount'}:
            self.update_journal_entry()

        return result

    def update_journal_entry(self):
        """
        Update the journal entry associated with this ledger payment.
        """
        self.ensure_one()

        # If there is no linked journal entry, skip
        if not self.journal_entry_id:
            return

        # Update the journal entry with new values
        self.journal_entry_id.write({
            'date': self.date,
            'ref': self.name,
            'journal_id': self.journal_id.id,
        })

        # Update the journal items based on the new ledger payment data
        account_values = []

        self.journal_entry_id.line_ids = [(5, 0, 0)]

        if self.boole == 'receive':
            # Debit the first account (source account)
            account_values.append((0, 0, {
                'account_id': self.source_acc.id,
                'debit': self.amount,
                'credit': 0.0,
                'date': self.date,
            }))
            # Credit the second account (destination account)
            account_values.append((0, 0, {
                'account_id': self.dest_acc.id,
                'debit': 0.0,
                'credit': self.amount,
                'date': self.date,
            }))
        elif self.boole == 'send':
            # Credit the first account (source account)
            account_values.append((0, 0, {
                'account_id': self.source_acc.id,
                'debit': 0.0,
                'credit': self.amount,
                'date': self.date,
            }))
            # Debit the second account (destination account)
            account_values.append((0, 0, {
                'account_id': self.dest_acc.id,
                'debit': self.amount,
                'credit': 0.0,
                'date': self.date,
            }))

        # Write the updated journal items to the journal entry
        self.journal_entry_id.write({
            'line_ids': account_values,
        })

        return True

    # @api.depends('bank_manual_line_ids.is_manual_reconcile', 'bank_manual_line_ids.amount')
    # def _compute_amount(self):
    #     for order in self:
    #         reconciled_amount = sum(line.manual_reconcile_amount for line in order.bank_manual_line_ids if line.is_manual_reconcile)
    #         order.reconciled_amount = reconciled_amount

    # def submit_reconciliation_records(self):
    #     for rec in self:
    #         remaining_amount = rec.amount

    #         # Filter and sort bank_manual_line_ids
    #         sorted_lines = rec.bank_manual_line_ids.filtered(lambda l: l.is_manual_reconcile).sorted(key=lambda l: l.amount)

    #         for line in sorted_lines:
    #             invoice = line.invoice_id
    #             line_manual_reconcile_amount = line.manual_reconcile_amount

    #             if line_manual_reconcile_amount <= remaining_amount:
    #                 line.manual_reconcile_amount = 0
    #                 invoice.manual_reconcile_amount = 0
    #                 invoice.is_manual_reconcile = True

    #                 remaining_amount -= line_manual_reconcile_amount
    #             else:
    #                 line.manual_reconcile_amount -= remaining_amount

    #                 invoice.manual_reconcile_amount -= remaining_amount

    #                 remaining_amount = 0

    #         self.state = 'recocile'
    #         if rec.amount > rec.reconciled_amount:
    #             rec.amount_paid =  rec.amount - rec.reconciled_amount

    @api.depends('bank_manual_line_ids.is_manual_reconcile', 'bank_manual_line_ids.amount')
    def _compute_amount(self):
        for order in self:
            reconciled_amount = sum(
                line.manual_reconcile_amount for line in order.bank_manual_line_ids if line.is_manual_reconcile)
            order.reconciled_amount = reconciled_amount

    def submit_reconciliation_records(self):
        for rec in self:
            # if rec.amount == rec.reconciled_amount:
            remaining_amount = rec.amount

            # Filter and sort bank_manual_line_ids
            sorted_lines = rec.bank_manual_line_ids.filtered(lambda l: l.is_manual_reconcile).sorted(
                key=lambda l: l.amount)

            false_lines = rec.bank_manual_line_ids.filtered(lambda l: not l.is_manual_reconcile)
            false_lines.unlink()

            for line in sorted_lines:
                invoice = line.invoice_id
                line_manual_reconcile_amount = line.manual_reconcile_amount

                if line_manual_reconcile_amount <= remaining_amount:
                    if line.commsn != 0:
                        line.manual_reconcile_amount = line.commsn
                        invoice.manual_reconcile_amount = line.commsn
                        rec.amount_paid += line.manual_reconcile_amount

                        invoice.is_manual_reconcile = False

                        remaining_amount -= line_manual_reconcile_amount
                        line.commsn = 0


                    else:
                        line.manual_reconcile_amount = 0
                        invoice.manual_reconcile_amount = 0
                        invoice.is_manual_reconcile = True

                        remaining_amount -= line_manual_reconcile_amount
            # if rec.amount == rec.reconciled_amount:

            self.state = 'recocile'

            # else:
            #     raise ValidationError("Reconciled amount should match with the amount. Please check the reconciled amount.")


class BankAccountManualLine(models.Model):
    _name = 'bank.account.manual.line'

    ledger_pay_id = fields.Many2one('ledger.payment', string="Bank Manual ID:")
    name = fields.Char(string="Invoice Number")
    date = fields.Date(string="Invoice Date")
    provider_reference = fields.Char(string="Razorpay ref id")
    amount = fields.Float(string="Amount")
    commsn = fields.Float(string="Commsn", )
    customer_name = fields.Char(string="Customer Name")
    is_manual_reconcile = fields.Boolean(string='Reconciled', default=False)
    invoice_id = fields.Many2one('account.move', string='Invoice Id')
    manual_reconcile_amount = fields.Float(string='Reconcile Amount')

    @api.onchange('manual_reconcile_amount')
    def _onchange_manual_reconcile_amount(self):
        for line in self:
            if line.manual_reconcile_amount:
                line.commsn = line.amount - line.manual_reconcile_amount
