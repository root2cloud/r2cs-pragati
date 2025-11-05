from odoo import models, _
from odoo.exceptions import UserError
import xlsxwriter
import base64
from io import BytesIO


class PosDetailsWizard(models.TransientModel):
    _inherit = 'pos.details.wizard'

    def action_export_xlsx(self):
        if not self.start_date or not self.end_date:
            raise UserError(_("Please select both Start Date and End Date."))

        orders = self.env['pos.order'].search([
            ('session_id.config_id', 'in', self.pos_config_ids.ids),
            ('date_order', '>=', self.start_date),
            ('date_order', '<=', self.end_date),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])

        if not orders:
            raise UserError(_('No POS Orders found for the selected criteria.'))

        # Initialize workbook
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Sales Details")

        bold = workbook.add_format({'bold': True})
        currency = workbook.add_format({'num_format': '#,##0.00'})

        row = 0

        # Title and date
        sheet.write(row, 0, "Sales Details", bold)
        row += 1
        sheet.write(row, 0, f"{self.start_date.strftime('%d/%m/%Y %H:%M:%S')} - {self.end_date.strftime('%d/%m/%Y %H:%M:%S')}")
        row += 2

        # === PRODUCTS SECTION ===
        sheet.write(row, 0, "Products", bold)
        row += 1

        product_headers = ['Product', 'Quantity', 'Price Unit', 'Discount (%)', 'Value (After Discount)']
        for col, header in enumerate(product_headers):
            sheet.write(row, col, header, bold)
        row += 1

        total_discount = 0.0
        for order in orders:
            for line in order.lines:
                discount_amt = (line.qty * line.price_unit) * (line.discount / 100.0)
                net_value = (line.qty * line.price_unit) - discount_amt
                product_name = f"[{line.product_id.default_code}] {line.product_id.name}" if line.product_id.default_code else line.product_id.name

                sheet.write(row, 0, product_name)
                sheet.write(row, 1, line.qty)
                sheet.write(row, 2, line.price_unit, currency)
                sheet.write(row, 3, line.discount)
                sheet.write(row, 4, net_value, currency)

                total_discount += discount_amt
                row += 1

        row += 2

        # === PAYMENTS SECTION ===
        sheet.write(row, 0, "Payments", bold)
        row += 1
        sheet.write(row, 0, "Name", bold)
        sheet.write(row, 1, "Total", bold)
        row += 1

        payments = {}
        for order in orders:
            for payment in order.payment_ids:
                name = payment.payment_method_id.name
                payments[name] = payments.get(name, 0.0) + payment.amount
        for name, total in payments.items():
            sheet.write(row, 0, name)
            sheet.write(row, 1, total, currency)
            row += 1

        row += 2

        # === TAXES SECTION ===
        sheet.write(row, 0, "Taxes", bold)
        row += 1
        sheet.write(row, 0, "Name", bold)
        sheet.write(row, 1, "Tax Amount", bold)
        sheet.write(row, 2, "Base Amount", bold)
        row += 1

        taxes = {}
        for order in orders:
            for line in order.lines:
                tax_details = line.tax_ids_after_fiscal_position.compute_all(
                    line.price_unit, order.currency_id, line.qty, line.product_id
                )
                for tax in tax_details['taxes']:
                    name = tax['name']
                    taxes.setdefault(name, {'amount': 0.0, 'base': 0.0})
                    taxes[name]['amount'] += tax['amount']
                    taxes[name]['base'] += tax['base']
        for name, vals in taxes.items():
            sheet.write(row, 0, name)
            sheet.write(row, 1, vals['amount'], currency)
            sheet.write(row, 2, vals['base'], currency)
            row += 1

        row += 2

        # === DISCOUNT SUMMARY ===
        sheet.write(row, 0, "Discounts", bold)
        row += 1
        sheet.write(row, 0, "Total Discounts:", bold)
        sheet.write(row, 1, total_discount, currency)

        row += 2

        # === GRAND TOTAL SECTION ===
        total_paid = sum(order.amount_total for order in orders)
        sheet.write(row, 0, "Total:", bold)
        sheet.write(row, 1, total_paid, currency)

        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': 'pos_sales_details_report.xlsx',
            'type': 'binary',
            'datas': xlsx_data,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
