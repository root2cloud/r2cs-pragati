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

        Now includes Initial Balance section at top with Initial Balance, Debit, Credit, Balance columns
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
        sheet.set_column(0, 0, 15)  # Date
        sheet.set_column(1, 1, 12)  # JRNL
        sheet.set_column(2, 2, 30)  # Partner
        sheet.set_column(3, 3, 18)  # Ref No
        sheet.set_column(4, 4, 50)  # Narration
        sheet.set_column(5, 5, 20)  # Initial Balance
        sheet.set_column(6, 6, 15)  # Debit
        sheet.set_column(7, 7, 15)  # Credit
        sheet.set_column(8, 8, 15)  # Balance
        sheet.set_column(9, 9, 25)  # Company Name

        # Formats
        header_fmt = workbook.add_format({'bold': True, 'align': 'center', 'font_size': 10, 'font': 'Arial'})
        header_light_fmt = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 9, 'font': 'Arial', 'bg_color': '#D3D3D3'})
        cell_left = workbook.add_format({'align': 'left', 'font_size': 10, 'font': 'Arial'})
        cell_center = workbook.add_format({'align': 'center', 'font_size': 10, 'font': 'Arial'})
        num_fmt = workbook.add_format({'align': 'right', 'font_size': 10, 'font': 'Arial'})
        num_fmt.set_num_format('#,##0.00')
        total_fmt = workbook.add_format({'align': 'right', 'font_size': 10, 'font': 'Arial', 'bold': True, 'top': 2})
        total_fmt.set_num_format('#,##0.00')

        # Header row
        row = 0
        sheet.write(row, 0, _('Date'), header_fmt)
        sheet.write(row, 1, _('JRNL'), header_fmt)
        sheet.write(row, 2, _('Partner'), header_fmt)
        sheet.write(row, 3, _('Ref No'), header_fmt)
        sheet.write(row, 4, _('Narration'), header_fmt)
        sheet.write(row, 5, _('Initial Balance'), header_fmt)
        sheet.write(row, 6, _('Debit'), header_fmt)
        sheet.write(row, 7, _('Credit'), header_fmt)
        sheet.write(row, 8, _('Balance'), header_fmt)
        sheet.write(row, 9, _('Company'), header_fmt)
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
            sheet.merge_range(row, 0, row, 9, account_name, cell_left)
            row += 1

            # ✅ EXTRACT INITIAL BALANCE VALUES
            initial_debit = 0.0
            initial_credit = 0.0
            initial_balance = 0.0
            found_initial = False

            # Method 1: Check if initial_bal exists in account_data as dictionary
            if isinstance(account_data.get('initial_bal'), dict):
                initial_data = account_data.get('initial_bal', {})
                initial_balance = float(initial_data.get('balance', 0))
                initial_debit = float(initial_data.get('debit', 0))
                initial_credit = float(initial_data.get('credit', 0))
                found_initial = True

            # Method 2: Search through lines array for initial_bal flag
            if not found_initial:
                for line in account_data.get('lines', []):
                    if line.get('initial_bal'):
                        initial_balance = float(line.get('balance', 0))
                        initial_debit = float(line.get('debit', 0))
                        initial_credit = float(line.get('credit', 0))
                        found_initial = True
                        break

            # Method 3: Calculate from account opening balance
            if not found_initial:
                total_debit = float(account_data.get('debit', 0))
                total_credit = float(account_data.get('credit', 0))
                total_balance = float(account_data.get('balance', 0))

                lines_debit = 0.0
                lines_credit = 0.0
                for line in account_data.get('lines', []):
                    if not line.get('initial_bal') and not line.get('ending_bal'):
                        lines_debit += float(line.get('debit', 0))
                        lines_credit += float(line.get('credit', 0))

                # Initial balance = Total balance - (Lines debit - Lines credit)
                initial_balance = total_balance - (lines_debit - lines_credit)
                initial_debit = total_debit - lines_debit
                initial_credit = total_credit - lines_credit

            # ✅ INITIAL BALANCE ROW - WITH DEBIT, CREDIT, AND BALANCE VALUES
            sheet.write(row, 0, '', cell_left)
            sheet.write(row, 1, '', cell_left)
            sheet.write(row, 2, '', cell_left)
            sheet.write(row, 3, '', cell_left)
            sheet.write(row, 4, _('Initial Balance'), header_light_fmt)
            sheet.write_number(row, 5, initial_balance, num_fmt)  # ✅ Initial Balance
            sheet.write_number(row, 6, initial_debit, num_fmt)  # ✅ Debit (accumulated)
            sheet.write_number(row, 7, initial_credit, num_fmt)  # ✅ Credit (accumulated)
            sheet.write_number(row, 8, initial_balance, num_fmt)  # ✅ Balance (same as initial)
            sheet.write(row, 9, '', cell_left)
            row += 1

            # Loop through each line (transaction details)
            # --- START FIX: Initialize running balance from the correctly calculated initial_balance ---
            running_balance = initial_balance
            # -------------------------------------------------------------------------------------------

            # Loop through each line (transaction details)
            for line in account_data.get('lines', []):
                # Skip initial balance and ending balance lines
                if line.get('initial_bal') or line.get('ending_bal'):
                    continue

                date = line.get('ldate')
                if date and isinstance(date, datetime.date):
                    date = date.strftime('%d-%m-%Y')

                # --- START FIX: Calculate running balance manually ---
                current_debit = float(line.get('debit', 0))
                current_credit = float(line.get('credit', 0))
                running_balance += current_debit - current_credit
                # ---------------------------------------------------

                # Write line details
                sheet.write(row, 0, date or '', cell_center)
                sheet.write(row, 1, line.get('lcode') or '', cell_center)
                sheet.write(row, 2, line.get('partner_name') or '', cell_left)
                sheet.write(row, 3, line.get('move_name') or '', cell_center)
                sheet.write(row, 4, line.get('lname') or '', cell_left)
                sheet.write(row, 5, '', cell_left)  # Empty - Initial Balance column for transaction rows

                sheet.write_number(row, 6, current_debit, num_fmt)
                sheet.write_number(row, 7, current_credit, num_fmt)

                # --- START FIX: Write the manually calculated running_balance ---
                sheet.write_number(row, 8, running_balance, num_fmt)
                # --------------------------------------------------------------

                # ✅ Add Company Name
                move = self.env['account.move'].browse(line.get('move_id')) if line.get('move_id') else False
                company_name = move.company_id.name if move and move.company_id else (ks_company_id.name or '')
                sheet.write(row, 9, company_name, cell_left)

                row += 1

            # Account totals
            sheet.write(row, 0, '', cell_left)
            sheet.write(row, 1, '', cell_left)
            sheet.write(row, 2, '', cell_left)
            sheet.write(row, 3, '', cell_left)
            sheet.write(row, 4, _('Total:'), header_fmt)
            sheet.write(row, 5, '', cell_left)
            sheet.write_number(row, 6, float(account_data.get('debit', 0)), total_fmt)
            sheet.write_number(row, 7, float(account_data.get('credit', 0)), total_fmt)
            sheet.write_number(row, 8, float(account_data.get('balance', 0)), total_fmt)
            sheet.write(row, 9, '', cell_left)
            row += 2

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file