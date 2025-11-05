from odoo import models, fields, api
from datetime import date

class StockLot(models.Model):
    _inherit = 'stock.lot'

    alert_date = fields.Date(string='Alert Date')

    expiry_state = fields.Selection([
        ('ok', 'OK'),
        ('alert', 'Alert')
    ], compute='_compute_expiry_state', store=True)

    @api.depends('alert_date', 'removal_date')
    def _compute_expiry_state(self):
        today = date.today()
        for rec in self:
            removal_date = rec.removal_date.date() if rec.removal_date else None
            if (removal_date and removal_date >= today and
                rec.alert_date and rec.alert_date <= today):
                rec.expiry_state = 'alert'
            else:
                rec.expiry_state = 'ok'

    @api.model
    def _check_lot_expiry_alerts(self):
        today = date.today()
        lots = self.search([('alert_date', '=', today)])
        if not lots:
            return

        # List of user logins to notify
        user_logins = [
            'acharyulu@pragatibiopharma.com',
            'bhargav.k@pragatibiopharma.com',
            'vasavi@pragatisparsh.com',
            'salepointresort@pragatibiopharma.com',
            'info@pragatisparsh.com',
        ]

        users = self.env['res.users'].search([('login', 'in', user_logins)])
        if not users:
            _logger = self.env['ir.logging']
            _logger.create({
                'name': 'Lot Expiry Cron',
                'type': 'server',
                'level': 'WARNING',
                'dbname': self._cr.dbname,
                'message': "None of the alert users were found.",
                'path': __name__,
                'func': '_check_lot_expiry_alerts',
                'line': 'N/A',
            })
            return

        partner_ids = users.mapped('partner_id.id')

        activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not activity_type:
            return

        for lot in lots:
            message = (
                f"🔔 <b>Expiry Alert</b><br/>"
                f"🔹 <b>Product:</b> {lot.product_id.display_name}<br/>"
                f"🔹 <b>Lot:</b> {lot.name}<br/>"
                f"🔹 <b>Expiration Date:</b> {lot.expiration_date or 'N/A'}"
            )

            # Post to chatter with all partners
            lot.message_post(
                body=message,
                partner_ids=partner_ids,
                message_type="notification",
                subtype_xmlid='mail.mt_note',
            )

            # Create activity for each user
            for user in users:
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get_id('stock.lot'),
                    'res_id': lot.id,
                    'activity_type_id': activity_type.id,
                    'summary': 'Product Expiry Alert',
                    'note': message,
                    'user_id': user.id,
                    'date_deadline': lot.alert_date or today,
                })
