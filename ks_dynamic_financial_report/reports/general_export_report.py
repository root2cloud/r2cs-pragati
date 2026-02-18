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
        Inherited to customize the General Ledger Excel export.

        Modifications:
        1. Split 'Account' column into separate 'Account Code' and 'Account Name' columns.
        2. Shifted all subsequent data columns by 2 positions to accommodate the split.
        3. Included detailed move lines (forced 'ks_report_with_lines').
        4. Added Company Name and Date Range headers.
        5. Added extra grouping columns (Main Group, Sub Group, Sub Sub Group).
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

        # Fetch bank accounts to identify BRS status
        bank_journals = self.env['account.journal'].search([('type', '=', 'bank')])
        bank_account_ids = bank_journals.mapped('default_account_id').ids

        # ====================================================================================
        # 1. SET COLUMN WIDTHS
        # ====================================================================================
        # NEW: Added specific widths for Code (0) and Name (1)
        sheet.set_column(0, 0, 15)  # Col 0: Account Code
        sheet.set_column(1, 1, 30)  # Col 1: Account Name

        # SHIFTED: All original columns shifted right by 2 positions (Original 0 -> New 2, etc.)
        sheet.set_column(2, 2, 12)  # Date
        sheet.set_column(3, 3, 20)  # Journal
        sheet.set_column(4, 4, 25)  # Partner
        sheet.set_column(5, 5, 18)  # Ref No
        sheet.set_column(6, 6, 10)  # Status
        sheet.set_column(7, 7, 12)  # BRS Status
        sheet.set_column(8, 8, 25)  # Reference
        sheet.set_column(9, 9, 30)  # Narration
        sheet.set_column(10, 10, 40)  # Corresponding Accounts
        sheet.set_column(11, 14, 15)  # Amounts: Init Bal, Debit, Credit, Balance

        # NEW: Extra Grouping Columns
        sheet.set_column(15, 15, 20)  # Main Group
        sheet.set_column(16, 16, 20)  # Sub Group
        sheet.set_column(17, 17, 20)  # Sub Sub Group

        # ====================================================================================
        # 2. DEFINE FORMATS
        # ====================================================================================
        header_fmt = workbook.add_format(
            {'bold': True, 'align': 'center', 'font_size': 10, 'font': 'Arial', 'border': 1, 'bg_color': '#D3D3D3'})
        cell_left = workbook.add_format({'align': 'left', 'font_size': 10, 'font': 'Arial', 'border': 1})
        cell_center = workbook.add_format({'align': 'center', 'font_size': 10, 'font': 'Arial', 'border': 1})
        cell_text_wrap = workbook.add_format(
            {'align': 'left', 'valign': 'top', 'font_size': 10, 'font': 'Arial', 'border': 1, 'text_wrap': True})
        num_fmt = workbook.add_format(
            {'align': 'right', 'font_size': 10, 'font': 'Arial', 'border': 1, 'num_format': '[$₹-4009] #,##0.00'})
        total_fmt = workbook.add_format(
            {'align': 'right', 'font_size': 10, 'font': 'Arial', 'bold': True, 'border': 1, 'top': 2,
             'num_format': '[$₹-4009] #,##0.00'})

        # Format: Positive (Dr); Negative (Cr)
        balance_fmt = workbook.add_format({
            'align': 'right',
            'font_size': 10,
            'font': 'Arial',
            'border': 1,
            'num_format': '[$₹-4009] #,##0.00 "Dr";[$₹-4009] #,##0.00 "Cr"'
        })

        total_balance_fmt = workbook.add_format({
            'align': 'right',
            'font_size': 10,
            'font': 'Arial',
            'bold': True,
            'border': 1,
            'top': 2,
            'num_format': '[$₹-4009] #,##0.00 "Dr";[$₹-4009] #,##0.00 "Cr"'
        })
        account_header_fmt = workbook.add_format(
            {'bold': True, 'align': 'left', 'font_size': 10, 'font': 'Arial', 'border': 1, 'bg_color': '#F2F2F2'})

        date_header_fmt = workbook.add_format({'bold': True, 'font_size': 10, 'font': 'Arial', 'align': 'left'})
        date_val_fmt = workbook.add_format({'font_size': 10, 'font': 'Arial', 'align': 'left'})

        # ====================================================================================
        # 3. REPORT HEADER (Company & Date)
        # ====================================================================================
        row = 0
        ks_company_name = ks_company_id.name if ks_company_id else ''
        company_header_fmt = workbook.add_format({'bold': True, 'font_size': 16, 'font': 'Arial', 'align': 'center'})

        # Merge range extended to 17 (Total columns = 18)
        sheet.merge_range(row, 0, row, 17, ks_company_name, company_header_fmt)
        row += 2

        if ks_df_informations.get('date'):
            lang = self.env.user.lang
            lang_rec = self.env['res.lang'].search([('code', '=', lang)], limit=1)
            date_format = lang_rec.date_format.replace('/', '-') if lang_rec else '%Y-%m-%d'

            ks_start_date = ks_df_informations['date'].get('ks_start_date')
            ks_end_date = ks_df_informations['date'].get('ks_end_date')

            date_center_fmt = workbook.add_format({'font_size': 11, 'font': 'Arial', 'align': 'center', 'bold': True})
            date_str = ""
            if ks_start_date and ks_end_date:
                start_date_obj = datetime.datetime.strptime(ks_start_date, '%Y-%m-%d').date()
                end_date_obj = datetime.datetime.strptime(ks_end_date, '%Y-%m-%d').date()
                date_str = _("Period: %s To %s") % (start_date_obj.strftime(date_format),
                                                    end_date_obj.strftime(date_format))
            elif ks_end_date:
                end_date_obj = datetime.datetime.strptime(ks_end_date, '%Y-%m-%d').date()
                date_str = _("As of Date: %s") % end_date_obj.strftime(date_format)

            if date_str:
                # Merge range extended to 17
                sheet.merge_range(row, 0, row, 17, date_str, date_center_fmt)

            row += 2

        # ====================================================================================
        # 4. TABLE HEADERS
        # ====================================================================================
        headers = [
            # CHANGE: Added explicit Code and Name headers first
            _('Account Code'),
            _('Account Name'),
            # SHIFTED: Previous headers moved down
            _('Date'), _('Journal'), _('Partner'), _('Ref No'),
            _('Status'), _('BRS Status'), _('Reference'),
            _('Narration'), _('Corresponding Accounts'),
            _('Initial Balance'), _('Debit'), _('Credit'), _('Balance'),
            # NEW: Grouping headers
            _('Main Group'), _('Sub Group'), _('Sub Sub Group'),
        ]

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_fmt)
        row += 1

        if not move_lines:
            workbook.close()
            output.seek(0)
            return output.read()

        # ====================================================================================
        # 5. DATA LOOPS
        # ====================================================================================
        for account_key, account_data in move_lines[0].items():

            # --------------------------------------------------------------------------------
            # 5.1 ACCOUNT HEADER ROW (Gray Separator)
            # --------------------------------------------------------------------------------
            # CHANGE: Write 'Code' and 'Name' in separate columns (0 & 1) instead of merging
            sheet.write(row, 0, account_data.get('code') or '', account_header_fmt)
            sheet.write(row, 1, account_data.get('name') or '', account_header_fmt)

            # Merge the remaining "transaction" space (Col 2 to 14) with empty gray background
            sheet.merge_range(row, 2, row, 14, '', account_header_fmt)

            # Write Groups in the new columns (15-17)
            sheet.write(row, 15, account_data.get('main_group') or '', cell_center)
            sheet.write(row, 16, account_data.get('sub_group') or '', cell_center)
            sheet.write(row, 17, account_data.get('sub_sub_group') or '', cell_center)
            row += 1

            # --------------------------------------------------------------------------------
            # 5.2 CALCULATE INITIAL BALANCE
            # --------------------------------------------------------------------------------
            initial_balance = 0.0
            found_initial = False

            # Method 1: Direct key
            if isinstance(account_data.get('initial_bal'), dict):
                initial_data = account_data.get('initial_bal', {})
                initial_balance = float(initial_data.get('balance', 0))
                found_initial = True

            # Method 2: From lines
            if not found_initial:
                for line in account_data.get('lines', []):
                    if line.get('initial_bal'):
                        initial_balance = float(line.get('balance', 0))
                        found_initial = True
                        break

            # Method 3: Computation
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

            # --------------------------------------------------------------------------------
            # 5.3 WRITE INITIAL BALANCE ROW
            # --------------------------------------------------------------------------------
            # CHANGE: Col 0 & 1 are empty for Code/Name
            sheet.write(row, 0, '', cell_left)
            sheet.write(row, 1, '', cell_left)

            # Fill empty transaction columns (2-10)
            for i in range(2, 11):
                sheet.write(row, i, '', cell_left)

            # Write Amounts (Indices shifted +2)
            sheet.write_number(row, 11, initial_balance, balance_fmt)  # Was 9
            sheet.write(row, 12, '', cell_left)  # Was 10
            sheet.write(row, 13, '', cell_left)  # Was 11
            sheet.write_number(row, 14, initial_balance, balance_fmt)  # Was 12

            # Fill empty group columns (15-17)
            sheet.write(row, 15, '', cell_left)
            sheet.write(row, 16, '', cell_left)
            sheet.write(row, 17, '', cell_left)
            row += 1

            running_balance = initial_balance

            # --------------------------------------------------------------------------------
            # 5.4 TRANSACTION LINES LOOP
            # --------------------------------------------------------------------------------
            for line in account_data.get('lines', []):
                if line.get('initial_bal') or line.get('ending_bal'):
                    continue

                date = line.get('ldate')
                if date and isinstance(date, datetime.date):
                    date = date.strftime('%d-%m-%Y')

                current_debit = float(line.get('debit', 0))
                current_credit = float(line.get('credit', 0))
                running_balance += current_debit - current_credit

                # Format Corresponding Accounts
                corr_accounts = line.get('corresponding_accounts') or ''
                if corr_accounts:
                    corr_accounts = corr_accounts.replace(', ', '\n')

                # BRS Status
                if account_data.get('id') in bank_account_ids:
                    brs_status = 'Cleared' if line.get('is_brs_cleared') else 'Pending'
                else:
                    brs_status = ''

                # CHANGE: Shifted all data writing by +2 columns
                sheet.write(row, 0, '', cell_left)  # Empty Code
                sheet.write(row, 1, '', cell_left)  # Empty Name

                sheet.write(row, 2, date or '', cell_center)  # Was 0
                sheet.write(row, 3, line.get('lcode') or '', cell_center)  # Was 1
                sheet.write(row, 4, line.get('partner_name') or '', cell_left)  # Was 2
                sheet.write(row, 5, line.get('move_name') or '', cell_center)  # Was 3
                sheet.write(row, 6, line.get('move_state') or '', cell_center)  # Was 4
                sheet.write(row, 7, brs_status, cell_center)  # Was 5
                sheet.write(row, 8, line.get('lref') or '', cell_text_wrap)  # Was 6
                sheet.write(row, 9, line.get('lname') or '', cell_text_wrap)  # Was 7
                sheet.write(row, 10, corr_accounts, cell_text_wrap)  # Was 8

                sheet.write(row, 11, '', cell_left)  # Init Bal
                sheet.write_number(row, 12, current_debit, num_fmt)  # Debit
                sheet.write_number(row, 13, current_credit, num_fmt)  # Credit
                sheet.write_number(row, 14, running_balance, balance_fmt)  # Balance

                # Empty Groups
                sheet.write(row, 15, '', cell_left)
                sheet.write(row, 16, '', cell_left)
                sheet.write(row, 17, '', cell_left)

                row += 1

            # --------------------------------------------------------------------------------
            # 5.5 ACCOUNT TOTALS
            # --------------------------------------------------------------------------------
            # Write empty cells for 0-9
            for i in range(10):
                sheet.write(row, i, '', cell_left)

            sheet.write(row, 10, _('Total:'), header_fmt)  # Label
            # Amounts shifted +2
            sheet.write_number(row, 12, float(account_data.get('debit', 0)), total_fmt)
            sheet.write_number(row, 13, float(account_data.get('credit', 0)), total_fmt)
            sheet.write_number(row, 14, float(account_data.get('balance', 0)), balance_fmt)

            # Empty Groups
            sheet.write(row, 15, '', cell_left)
            sheet.write(row, 16, '', cell_left)
            sheet.write(row, 17, '', cell_left)
            row += 2

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file