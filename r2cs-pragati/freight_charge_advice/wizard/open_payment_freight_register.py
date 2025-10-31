from odoo import models, fields, api


class OpenPaymentRegisterWizard(models.TransientModel):
    _name = 'open.payment.freight.register.wizard'
    _description = 'Register freight Payment Wizard'

    journal_id = fields.Many2one('account.journal', string='Journal')
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Payment Method',
        readonly=False, store=True,
        compute='_compute_payment_method_line_id',
        domain="[('id', 'in', available_payment_method_line_ids)]",
        help="Manual: Pay or Get paid by any method outside of Odoo.\n"
        "Payment Providers: Each payment provider has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
        "Check: Pay bills by check and print it from Odoo.\n"
        "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
        "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
        "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    amount = fields.Float(string='Amount')
    payment_date = fields.Date(string='Payment Date', default=fields.Datetime.now)
    communication = fields.Char(string='Memo')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    partner_bank_id = fields.Many2one('res.partner.bank', string='Receipent Bank Account')
    advice_id = fields.Many2one('freight.charge.advice', string='Advice Id')
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_payment_method_line_fields')

    payment_type = fields.Selection([
            ('outbound', 'Send'),
            ('inbound', 'Receive'),
        ], string='Payment Type', default='inbound', required=True, tracking=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_compute_currency_id', store=True, readonly=False, precompute=True,
        help="The payment's currency.")



    @api.depends('payment_type', 'journal_id', 'currency_id')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            if wizard.journal_id:
                wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)
            else:
                wizard.available_payment_method_line_ids = False


    def action_create_payment(self):
        for rec in self:
            payment = self.env['account.payment'].create({
                'journal_id': self.journal_id.id,
                'payment_type': 'outbound',  # Changed to 'outbound' for vendor payment
                'partner_type': 'supplier',  # Added partner_type for vendor payment
                'partner_id': self.partner_id.id,
                'amount': self.amount,
                'freight_advice_id': self.advice_id.id,
                'payment_method_line_id': self.payment_method_line_id.id,
                'partner_bank_id': self.partner_bank_id.id,
                'date': self.payment_date,
                'ref': self.communication
            })
            payment.action_post()
            if payment:
                self.advice_id.state = 'payment'
        return payment



    @api.depends('payment_type', 'journal_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            if wizard.journal_id:
                available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines(wizard.payment_type)
            else:
                available_payment_method_lines = False

            # Select the first available one by default.
            if available_payment_method_lines:
                wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False


    @api.depends('journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.journal_id.currency_id or pay.journal_id.company_id.currency_id