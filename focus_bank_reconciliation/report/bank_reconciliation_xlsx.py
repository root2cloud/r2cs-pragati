# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError
import io
import base64

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class BankReconciliationXlsx(models.AbstractModel):
    _name = 'report.focus_bank_reconciliation.report_bank_xlsx'
    _description = 'Bank Reconciliation Excel Report'

    def create_xlsx_report(self, doc):
        if not xlsxwriter:
            raise UserError(_("The 'xlsxwriter' python module is required to generate Excel files."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Reconciliation')

        # --- Styles ---
        style_title = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'})
        style_label = workbook.add_format({'bold': True, 'font_color': '#666666'})
        style_value = workbook.add_format({'bold': True})
        style_date = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        style_currency = workbook.add_format({'num_format': '#,##0.00'})

        # Table Header Style
        style_th = workbook.add_format({
            'bold': True,
            'border': 1,
            'bg_color': '#f0f0f0',
            'align': 'center',
            'valign': 'vcenter'
        })

        # Table Data Styles
        style_td = workbook.add_format({'border': 1})
        style_td_date = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})
        style_td_curr = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        style_td_center = workbook.add_format({'border': 1, 'align': 'center'})

        # --- NEW STYLES FOR STATUS ---
        style_status_green = workbook.add_format({
            'border': 1,
            'align': 'center',
            'bold': True,
            'font_color': '#2e6b30',  # Green
            'bg_color': '#e6fffa'  # Light Green Background for better visibility
        })

        style_status_red = workbook.add_format({
            'border': 1,
            'align': 'center',
            'bold': True,
            'font_color': '#d9534f',  # Red
            'bg_color': '#fcebea'  # Light Red Background for better visibility
        })

        # Summary Box Styles
        style_box_book = workbook.add_format({'bold': True, 'font_size': 11})
        style_box_debit = workbook.add_format({'bold': True, 'font_size': 11, 'font_color': '#d9534f'})
        style_box_credit = workbook.add_format({'bold': True, 'font_size': 11, 'font_color': '#2e6b30'})
        style_box_diff_red = workbook.add_format({'bold': True, 'font_size': 11, 'font_color': 'red'})
        style_box_diff_green = workbook.add_format({'bold': True, 'font_size': 11, 'font_color': 'green'})

        # --- 1. Title & Parameters ---
        sheet.merge_range('A1:K1', 'Bank Reconciliation', style_title)

        sheet.write(2, 0, 'Bank Journal:', style_label)
        sheet.write(2, 1, doc.bank_journal_id.name, style_value)
        sheet.write(2, 2, 'Date From:', style_label)
        sheet.write(2, 3, doc.date_from, style_date)
        sheet.write(2, 4, 'Date To:', style_label)
        sheet.write(2, 5, doc.date_to, style_date)

        # --- 2. Summary Section ---
        # Column 1: Book Balance
        sheet.write(4, 0, 'Book Balance:', style_label)
        sheet.write(4, 1, doc.book_balance, style_box_book)
        sheet.write(5, 0, 'Opening Balance:', style_label)
        sheet.write(5, 1, doc.opening_balance, style_currency)

        # Column 2: Out Debits
        sheet.write(4, 3, 'Out Debits:', style_label)
        sheet.write(4, 4, doc.uncleared_debit_amount, style_box_debit)
        sheet.write(5, 3, 'Debits Count:', style_label)
        sheet.write(5, 4, doc.uncleared_debit_count, style_value)

        # Column 3: Out Credits
        sheet.write(4, 6, 'Out Credits:', style_label)
        sheet.write(4, 7, doc.uncleared_credit_amount, style_box_credit)
        sheet.write(5, 6, 'Credits Count:', style_label)
        sheet.write(5, 7, doc.uncleared_credit_count, style_value)

        # Column 4: Totals
        sheet.write(4, 9, 'Cleared Balance:', style_label)
        sheet.write(4, 10, doc.cleared_balance, style_box_credit)

        sheet.write(5, 9, 'Bank Balance:', style_label)
        sheet.write(5, 10, doc.balance_end_real, style_value)

        sheet.write(6, 9, 'Difference:', style_label)
        variance = doc.unreconciled_variance
        sheet.write(6, 10, variance, style_box_diff_red if variance != 0 else style_box_diff_green)

        # --- 3. Transactions List ---
        row = 9
        headers = [
            '#', 'Status', 'Clearance Date', 'Document No', 'Document Date',
            'Debit', 'Credit', 'Cheque No', 'Doc Type', 'Narration', 'Account'
        ]

        # Write Headers
        for col_num, header in enumerate(headers):
            sheet.write(row, col_num, header, style_th)
            sheet.set_column(col_num, col_num, 15)

            # Write Data
        row += 1

        sorted_lines = doc.line_ids.sorted(key=lambda r: r.brs_serial_no)

        for line in sorted_lines:
            # 0. Serial No
            sheet.write(row, 0, line.brs_serial_no, style_td_center)

            # 1. Status (Apply Conditional Formatting)
            status = 'Cleared' if line.is_brs_cleared else 'Pending'
            # Select style based on status
            status_style = style_status_green if line.is_brs_cleared else style_status_red
            sheet.write(row, 1, status, status_style)

            # 2. Clearance Date
            sheet.write(row, 2, line.brs_clearance_date or '', style_td_date)

            # 3. Document No
            sheet.write(row, 3, line.move_name or '', style_td)

            # 4. Document Date
            sheet.write(row, 4, line.date, style_td_date)

            # 5. Debit
            sheet.write(row, 5, line.debit, style_td_curr)

            # 6. Credit
            sheet.write(row, 6, line.credit, style_td_curr)

            # 7. Cheque No
            sheet.write(row, 7, line.cheque_number or '', style_td)

            # 8. Document Type
            sheet.write(row, 8, line.brs_document_type or '', style_td)

            # 9. Narration
            sheet.write(row, 9, line.narration or '', style_td)

            # 10. Account
            sheet.write(row, 10, line.brs_counterpart_account or '', style_td)

            row += 1

        # --- 4. Finalize ---
        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        attachment = self.env['ir.attachment'].create({
            'name': f'Bank_Reconciliation_{doc.date_to}.xlsx',
            'type': 'binary',
            'datas': file_data,
            'res_model': 'bank.reconciliation.console',
            'res_id': doc.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
