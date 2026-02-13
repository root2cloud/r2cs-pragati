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
        - Added 'Corresp. Acc' column

        Now includes Initial Balance section at top with Initial Balance, Debit, Credit, Balance columns
        """

        # Force "With Lines" mode so ks_process_general_ledger() returns transaction details
        ks_df_informations['ks_report_with_lines'] = True

        # Get processed move lines
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        move_lines = self.ks_process_general_ledger(ks_df_informations)
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

        # Create worksheet
        sheet = workbook.add_worksheet('General Ledger')
        # <--- ADD THIS --->
        bank_journals = self.env['account.journal'].search([('type', '=', 'bank')])
        bank_account_ids = bank_journals.mapped('default_account_id').ids
        # <--- END --->

        # --- 1. SET COLUMN WIDTHS ---
        sheet.set_column(0, 0, 12)  # Date
        sheet.set_column(1, 1, 25)  # JRNL
        sheet.set_column(2, 2, 25)  # Partner
        sheet.set_column(3, 3, 18)  # Ref No
        sheet.set_column(4, 4, 10)  # Status
        sheet.set_column(5, 5, 12)  # BRS Status
        sheet.set_column(6, 6, 25)  # Reference
        sheet.set_column(7, 7, 30)  # Narration
        sheet.set_column(8, 8, 40)  # Corresponding Accounts
        sheet.set_column(9, 12, 15)  # Amounts: Init Bal, Debit, Credit, Balance

        # --- NEW COLUMNS WIDTHS ---
        sheet.set_column(13, 13, 20)  # Main Group
        sheet.set_column(14, 14, 20)  # Sub Group
        sheet.set_column(15, 15, 20)  # Sub Sub Group
        sheet.set_column(16, 16, 25)  # Company (Shifted to 16)

        # --- 2. FORMATS ---
        header_fmt = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 10, 'font': 'Arial', 'border': 1, 'bg_color': '#D3D3D3'})
        header_light_fmt = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 9, 'font': 'Arial', 'bg_color': '#D3D3D3'})
        cell_left = workbook.add_format({'align': 'left', 'font_size': 10, 'font': 'Arial', 'border': 1})
        cell_center = workbook.add_format({'align': 'center', 'font_size': 10, 'font': 'Arial', 'border': 1})
        cell_text_wrap = workbook.add_format(
            {'align': 'left', 'valign': 'top', 'font_size': 10, 'font': 'Arial', 'border': 1, 'text_wrap': True})
        num_fmt = workbook.add_format(
            {'align': 'right', 'font_size': 10, 'font': 'Arial', 'border': 1, 'num_format': '[$₹-4009] #,##0.00'})
        total_fmt = workbook.add_format(
            {'align': 'right', 'font_size': 10, 'font': 'Arial', 'bold': True, 'border': 1, 'top': 2,
             'num_format': '[$₹-4009] #,##0.00'})
        account_header_fmt = workbook.add_format(
            {'bold': True, 'align': 'left', 'font_size': 10, 'font': 'Arial', 'border': 1, 'bg_color': '#F2F2F2'})

        date_header_fmt = workbook.add_format({'bold': True, 'font_size': 10, 'font': 'Arial', 'align': 'left'})
        date_val_fmt = workbook.add_format({'font_size': 10, 'font': 'Arial', 'align': 'left'})

        # --- 3. HEADER ROW ---
        row = 0
        # <--- INSERT THIS BLOCK --->
        if ks_df_informations.get('date'):
            lang = self.env.user.lang
            lang_rec = self.env['res.lang'].search([('code', '=', lang)], limit=1)
            date_format = lang_rec.date_format.replace('/', '-') if lang_rec else '%Y-%m-%d'

            ks_start_date = ks_df_informations['date'].get('ks_start_date')
            ks_end_date = ks_df_informations['date'].get('ks_end_date')

            if ks_start_date:
                start_date_obj = datetime.datetime.strptime(ks_start_date, '%Y-%m-%d').date()
                formatted_start = start_date_obj.strftime(date_format)
                sheet.write(row, 0, _('Date from:'), date_header_fmt)
                sheet.write(row, 1, formatted_start, date_val_fmt)

            if ks_end_date:
                end_date_obj = datetime.datetime.strptime(ks_end_date, '%Y-%m-%d').date()
                formatted_end = end_date_obj.strftime(date_format)
                sheet.write(row, 2, _('Date to:'), date_header_fmt)
                sheet.write(row, 3, formatted_end, date_val_fmt)

            row += 2  # Add spacing before table headers
        # <--- END INSERT --->

        headers = [
            _('Date'), _('Journal'), _('Partner'), _('Ref No'),
            _('Status'), _('BRS Status'), _('Reference'),
            _('Narration'), _('Corresponding Accounts'),
            _('Initial Balance'), _('Debit'), _('Credit'), _('Balance'),
            # Added new Headers
            _('Main Group'), _('Sub Group'), _('Sub Sub Group'),
            _('Company')
        ]

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_fmt)
        row += 1

        if not move_lines:
            workbook.close()
            output.seek(0)
            return output.read()

        # Loop through accounts
        for account_key, account_data in move_lines[0].items():
            # Account header
            account_name = f"{account_data.get('code')} - {account_data.get('name')}"

            # Merge up to Balance column (Index 12)
            sheet.merge_range(row, 0, row, 12, account_name, account_header_fmt)

            # --- WRITE GROUP DATA IN THE ACCOUNT HEADER ROW ---
            sheet.write(row, 13, account_data.get('main_group') or '', cell_center)
            sheet.write(row, 14, account_data.get('sub_group') or '', cell_center)
            sheet.write(row, 15, account_data.get('sub_sub_group') or '', cell_center)
            sheet.write(row, 16, '', cell_left)  # Empty Company on header

            row += 1

            # --- CALCULATE INITIAL BALANCE ---
            initial_balance = 0.0
            found_initial = False

            # Method 1
            if isinstance(account_data.get('initial_bal'), dict):
                initial_data = account_data.get('initial_bal', {})
                initial_balance = float(initial_data.get('balance', 0))
                found_initial = True

            # Method 2
            if not found_initial:
                for line in account_data.get('lines', []):
                    if line.get('initial_bal'):
                        initial_balance = float(line.get('balance', 0))
                        found_initial = True
                        break

            # Method 3
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
                initial_balance = total_balance - (lines_debit - lines_credit)

            # --- 4. WRITE INITIAL BALANCE ROW ---
            sheet.write(row, 0, '', cell_left)
            sheet.write(row, 1, '', cell_left)
            sheet.write(row, 2, '', cell_left)
            sheet.write(row, 3, '', cell_left)
            sheet.write(row, 4, '', cell_left)  # Status
            sheet.write(row, 5, '', cell_left)  # BRS
            sheet.write(row, 6, '', cell_left)  # Ref
            sheet.write(row, 7, '', cell_left)  # Narration
            sheet.write(row, 8, '', cell_left)  # Corresp Acc
            sheet.write_number(row, 9, initial_balance, num_fmt)  # Initial Balance
            sheet.write(row, 10, '', cell_left)  # Debit (Empty as per view)
            sheet.write(row, 11, '', cell_left)  # Credit (Empty as per view)
            sheet.write_number(row, 12, initial_balance, num_fmt)  # Balance

            # Write empty cells for Groups and Company
            sheet.write(row, 13, '', cell_left)
            sheet.write(row, 14, '', cell_left)
            sheet.write(row, 15, '', cell_left)
            sheet.write(row, 16, '', cell_left)
            row += 1

            running_balance = initial_balance

            # Loop through lines
            for line in account_data.get('lines', []):
                if line.get('initial_bal') or line.get('ending_bal'):
                    continue

                date = line.get('ldate')
                if date and isinstance(date, datetime.date):
                    date = date.strftime('%d-%m-%Y')

                current_debit = float(line.get('debit', 0))
                current_credit = float(line.get('credit', 0))
                running_balance += current_debit - current_credit

                # Format Corresponding Accounts (Line by line)
                corr_accounts = line.get('corresponding_accounts') or ''
                if corr_accounts:
                    corr_accounts = corr_accounts.replace(', ', '\n')

                # Check if this account is a bank account
                if account_data.get('id') in bank_account_ids:
                    brs_status = 'Cleared' if line.get('is_brs_cleared') else 'Pending'
                else:
                    brs_status = ''  # Empty for non-bank accounts
                # --- 5. WRITE TRANSACTION LINE ---
                sheet.write(row, 0, date or '', cell_center)
                sheet.write(row, 1, line.get('lcode') or '', cell_center)
                sheet.write(row, 2, line.get('partner_name') or '', cell_left)
                sheet.write(row, 3, line.get('move_name') or '', cell_center)
                sheet.write(row, 4, line.get('move_state') or '', cell_center)
                sheet.write(row, 5, brs_status, cell_center)
                sheet.write(row, 6, line.get('lref') or '', cell_text_wrap)
                sheet.write(row, 7, line.get('lname') or '', cell_text_wrap)
                sheet.write(row, 8, corr_accounts, cell_text_wrap)

                sheet.write(row, 9, '', cell_left)  # Init Bal (Empty)
                sheet.write_number(row, 10, current_debit, num_fmt)
                sheet.write_number(row, 11, current_credit, num_fmt)
                sheet.write_number(row, 12, running_balance, num_fmt)

                move = self.env['account.move'].browse(line.get('move_id')) if line.get('move_id') else False
                company_name = move.company_id.name if move and move.company_id else (ks_company_id.name or '')

                # Write Empty for Groups on transaction lines
                sheet.write(row, 13, '', cell_left)
                sheet.write(row, 14, '', cell_left)
                sheet.write(row, 15, '', cell_left)

                # Write Company Name at column 16
                sheet.write(row, 16, company_name, cell_left)

                row += 1

            # --- 6. ACCOUNT TOTALS ---
            sheet.write(row, 0, '', cell_left)
            sheet.write(row, 1, '', cell_left)
            sheet.write(row, 2, '', cell_left)
            sheet.write(row, 3, '', cell_left)
            sheet.write(row, 4, '', cell_left)
            sheet.write(row, 5, '', cell_left)
            sheet.write(row, 6, '', cell_left)
            sheet.write(row, 7, '', cell_left)
            sheet.write(row, 8, '', cell_left)
            sheet.write(row, 9, _('Total:'), header_fmt)
            sheet.write_number(row, 10, float(account_data.get('debit', 0)), total_fmt)
            sheet.write_number(row, 11, float(account_data.get('credit', 0)), total_fmt)
            sheet.write_number(row, 12, float(account_data.get('balance', 0)), total_fmt)

            # Fill empty cells for new columns
            sheet.write(row, 13, '', cell_left)
            sheet.write(row, 14, '', cell_left)
            sheet.write(row, 15, '', cell_left)
            sheet.write(row, 16, '', cell_left)
            row += 2

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
