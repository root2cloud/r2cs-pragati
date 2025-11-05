# -*- coding: utf-8 -*-
from odoo import models, api, _
import io
import datetime
from odoo.tools.misc import xlsxwriter


class KsDynamicFinancialXlsxGLInherit(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    @api.model
    def ks_get_xlsx_general_ledger(self, ks_df_informations):
        """
        Inherited to always include detailed move lines (dropdown-like) in the General Ledger XLSX export,
        and include Company Name, with renamed columns:
        - 'Move' → 'Ref No'
        - 'Entry Label' → 'Narration'
        """

        # Force "With Lines" mode so ks_process_general_ledger() returns transaction details
        ks_df_informations['ks_report_with_lines'] = True

        # Get processed move lines
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        currency_id = self.env.user.company_id.currency_id
        move_lines = self.ks_process_general_ledger(ks_df_informations)
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

        # Create worksheet
        sheet = workbook.add_worksheet('General Ledger')
        sheet.set_column(0, 0, 12)   # Date
        sheet.set_column(1, 1, 12)   # JRNL
        sheet.set_column(2, 2, 30)   # Partner
        sheet.set_column(3, 3, 18)   # Ref No
        sheet.set_column(4, 4, 40)   # Narration
        sheet.set_column(5, 5, 10)   # Debit
        sheet.set_column(6, 6, 10)   # Credit
        sheet.set_column(7, 7, 10)   # Balance
        sheet.set_column(8, 8, 25)   # Company Name

        # Formats
        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 10, 'font': 'Arial'})
        cell_left = workbook.add_format({'align': 'left', 'font_size': 10, 'font': 'Arial'})
        cell_center = workbook.add_format({'align': 'center', 'font_size': 10, 'font': 'Arial'})
        num_fmt = workbook.add_format({'align': 'right', 'font_size': 10, 'font': 'Arial'})
        num_fmt.set_num_format('#,##0.00')

        # Header row
        row = 0
        sheet.write(row, 0, _('Date'), header_fmt)
        sheet.write(row, 1, _('JRNL'), header_fmt)
        sheet.write(row, 2, _('Partner'), header_fmt)
        sheet.write(row, 3, _('Ref No'), header_fmt)       # ✅ Renamed
        sheet.write(row, 4, _('Narration'), header_fmt)    # ✅ Renamed
        sheet.write(row, 5, _('Debit'), header_fmt)
        sheet.write(row, 6, _('Credit'), header_fmt)
        sheet.write(row, 7, _('Balance'), header_fmt)
        sheet.write(row, 8, _('Company'), header_fmt)
        row += 1

        # Ensure valid data
        if not move_lines:
            workbook.close()
            output.seek(0)
            return output.read()

        # Loop through accounts
        for account_key, account_data in move_lines[0].items():
            # Account header
            account_name = f"{account_data.get('code')} - {account_data.get('name')}"
            sheet.merge_range(row, 0, row, 8, account_name, cell_left)
            row += 1

            # Loop through each line
            for line in account_data.get('lines', []):
                if line.get('initial_bal') or line.get('ending_bal'):
                    continue

                date = line.get('ldate')
                if date and isinstance(date, datetime.date):
                    date = date.strftime('%d-%m-%Y')

                # Write line details
                sheet.write(row, 0, date or '', cell_center)
                sheet.write(row, 1, line.get('lcode') or '', cell_center)
                sheet.write(row, 2, line.get('partner_name') or '', cell_left)
                sheet.write(row, 3, line.get('move_name') or '', cell_center)   # ✅ Ref No
                sheet.write(row, 4, line.get('lname') or '', cell_left)         # ✅ Narration
                sheet.write_number(row, 5, float(line.get('debit', 0)), num_fmt)
                sheet.write_number(row, 6, float(line.get('credit', 0)), num_fmt)
                sheet.write_number(row, 7, float(line.get('balance', 0)), num_fmt)

                # ✅ Add Company Name
                move = self.env['account.move'].browse(line.get('move_id')) if line.get('move_id') else False
                company_name = move.company_id.name if move and move.company_id else (ks_company_id.name or '')
                sheet.write(row, 8, company_name, cell_left)

                row += 1

            # Account totals
            sheet.write(row, 4, _('Total:'), header_fmt)
            sheet.write_number(row, 5, float(account_data.get('debit', 0)), num_fmt)
            sheet.write_number(row, 6, float(account_data.get('credit', 0)), num_fmt)
            sheet.write_number(row, 7, float(account_data.get('balance', 0)), num_fmt)
            row += 2

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file