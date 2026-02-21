# -*- coding: utf-8 -*-
from odoo import models, api, _
import io
import re
from odoo.tools.misc import xlsxwriter
import datetime


class KsDynamicFinancialXlsxGLInherit(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    @api.model
    def ks_get_xlsx_general_ledger(self, ks_df_informations):
        ks_df_informations['ks_report_with_lines'] = True
        ks_df_informations['initial_balance'] = True

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        move_lines = self.ks_process_general_ledger(ks_df_informations)
        accounts_dict = move_lines[0] if isinstance(move_lines, tuple) else move_lines

        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

        sheet = workbook.add_worksheet('General Ledger')

        # ==========================================
        # 1. STRICT ACCOUNTING EXCEL FORMATS (WITH CURRENCY)
        # ==========================================
        title_fmt = workbook.add_format({'font_size': 14, 'bold': True, 'align': 'center', 'valign': 'vcenter'})
        subtitle_fmt = workbook.add_format({'font_size': 11, 'bold': True, 'align': 'center', 'valign': 'vcenter'})

        header_fmt = workbook.add_format({
            'bg_color': '#2d5b8c', 'font_color': '#ffffff', 'bold': True,
            'border': 1, 'border_color': '#555555',
            'align': 'center', 'valign': 'vcenter'
        })

        account_header_fmt = workbook.add_format({
            'bg_color': '#e2e6eb', 'bold': True, 'font_size': 11,
            'border': 1, 'border_color': '#7a7a7a',
            'align': 'left', 'valign': 'vcenter'
        })

        # STRICT Dr / Cr FORMATTING WITH RUPEE SYMBOL
        accounting_num_format = '[$₹-4009] #,##0.00 "Dr";[$₹-4009] #,##0.00 "Cr";"₹ 0.00"'
        standard_currency_fmt = '[$₹-4009] #,##0.00'

        init_bal_label_fmt = workbook.add_format({
            'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a',
            'align': 'right', 'valign': 'vcenter'
        })
        init_bal_num_fmt = workbook.add_format({
            'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a',
            'align': 'right', 'valign': 'vcenter', 'num_format': accounting_num_format
        })
        total_num_fmt = workbook.add_format({
            'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a',
            'align': 'right', 'valign': 'vcenter', 'num_format': standard_currency_fmt
        })
        init_bal_empty_fmt = workbook.add_format({
            'bg_color': '#f8f9fa', 'border': 1, 'border_color': '#7a7a7a',
        })

        cell_center = workbook.add_format(
            {'border': 1, 'border_color': '#7a7a7a', 'align': 'center', 'valign': 'vcenter'})

        # Changed valign to 'top' so if a row is tall, text starts at the top
        cell_left = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'left', 'valign': 'top'})
        cell_wrap = workbook.add_format(
            {'border': 1, 'border_color': '#7a7a7a', 'align': 'left', 'valign': 'top', 'text_wrap': True})

        num_fmt = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'right', 'valign': 'top',
                                       'num_format': standard_currency_fmt})
        balance_fmt = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'right', 'valign': 'top',
                                           'num_format': accounting_num_format, 'bold': True})

        # ==========================================
        # 2. DETERMINE BRS COLUMN VISIBILITY
        # ==========================================
        bank_journals = self.env['account.journal'].search([('type', '=', 'bank')])
        bank_account_ids = bank_journals.mapped('default_account_id').ids

        has_bank_acc = False
        for acc_key, acc_data in accounts_dict.items():
            if acc_key == 'Total' or not isinstance(acc_data, dict): continue
            if acc_data.get('id') in bank_account_ids:
                has_bank_acc = True
                break

        # ==========================================
        # 3. SET EXPANDED COLUMNS FOR CLEAR VISIBILITY
        # ==========================================
        headers = ['Date', 'Journal', 'Voucher', 'Accounts', 'Debit', 'Credit', 'Balance', 'Status',
                   'Reference / Narration']
        if has_bank_acc:
            headers.append('BRS Status')

        total_cols = len(headers)

        sheet.set_column(0, 0, 12)  # Date
        sheet.set_column(1, 1, 28)  # Journal (Increased width for better visibility)
        sheet.set_column(2, 2, 25)  # Voucher
        sheet.set_column(3, 3, 50)  # Accounts
        sheet.set_column(4, 5, 16)  # Debit, Credit
        sheet.set_column(6, 6, 20)  # Balance
        sheet.set_column(7, 7, 12)  # Status
        sheet.set_column(8, 8, 50)  # Ref/Narration
        if has_bank_acc:
            sheet.set_column(9, 9, 14)  # BRS

        # ==========================================
        # 4. PRINT REPORT TITLES
        # ==========================================
        row = 0
        sheet.merge_range(row, 0, row, total_cols - 1, ks_company_id.name, title_fmt)
        row += 1
        sheet.merge_range(row, 0, row, total_cols - 1, 'General Ledger', subtitle_fmt)
        row += 1

        # --- FIXED HEADER DATE LOGIC ---
        if ks_df_informations.get('date') and ks_df_informations['date'].get('ks_start_date'):
            s_date = str(ks_df_informations['date'].get('ks_start_date'))
            e_date = str(ks_df_informations['date'].get('ks_end_date'))

            # Safely convert YYYY-MM-DD to DD/MM/YYYY
            try:
                s_date = datetime.datetime.strptime(str(s_date)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                s_date = str(s_date)
            try:
                e_date = datetime.datetime.strptime(str(e_date)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                e_date = str(e_date)

            date_str = f"Period: {s_date} To {e_date}"
            sheet.merge_range(row, 0, row, total_cols - 1, date_str, subtitle_fmt)
        row += 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_fmt)
        row += 1

        sheet.freeze_panes(row, 0)

        # ==========================================
        # 5. PRINT TRANSACTION DATA
        # ==========================================
        for account_key, account_data in accounts_dict.items():
            if account_key == 'Total' or not isinstance(account_data, dict):
                continue

            is_bank_account = account_data.get('id') in bank_account_ids
            actual_code = account_data.get('code', account_key)
            actual_name = account_data.get('name', '')
            main_grp = account_data.get('main_group', 'N/A')
            sub_grp = account_data.get('sub_group', 'N/A')
            ss_grp = account_data.get('sub_sub_group', 'N/A')

            # Clean Account Header
            acc_header_text = f"Account: {actual_code} {actual_name}    [ Main Group: {main_grp}  |  Sub Group: {sub_grp}  |  Sub Sub Group: {ss_grp} ]"
            sheet.merge_range(row, 0, row, total_cols - 1, acc_header_text, account_header_fmt)
            row += 1

            total_debit = 0.0
            total_credit = 0.0

            has_init_bal = any(l.get('initial_bal') for l in account_data.get('lines', []))
            if not has_init_bal:
                forced_init_bal = account_data.get('initial_balance', 0.0)
                sheet.merge_range(row, 0, row, 3, "Initial Balance", init_bal_label_fmt)
                sheet.write(row, 4, '', init_bal_empty_fmt)
                sheet.write(row, 5, '', init_bal_empty_fmt)
                sheet.write_number(row, 6, forced_init_bal, init_bal_num_fmt)
                sheet.write(row, 7, '', init_bal_empty_fmt)
                sheet.write(row, 8, '', init_bal_empty_fmt)
                if has_bank_acc:
                    sheet.write(row, 9, '', init_bal_empty_fmt)
                row += 1

            for line in account_data.get('lines', []):
                if line.get('initial_bal'):
                    sheet.merge_range(row, 0, row, 3, "Initial Balance", init_bal_label_fmt)
                    sheet.write(row, 4, '', init_bal_empty_fmt)
                    sheet.write(row, 5, '', init_bal_empty_fmt)
                    sheet.write_number(row, 6, float(line.get('balance', 0.0)), init_bal_num_fmt)
                    sheet.write(row, 7, '', init_bal_empty_fmt)
                    sheet.write(row, 8, '', init_bal_empty_fmt)
                    if has_bank_acc:
                        sheet.write(row, 9, '', init_bal_empty_fmt)
                    row += 1

                elif line.get('ending_bal'):
                    continue

                else:
                    # ONE-LINE PER ACCOUNT USING \n
                    opp_acc_raw = str(line.get('corresponding_accounts') or '')
                    if opp_acc_raw:
                        raw_list = opp_acc_raw.split(', ')
                        clean_list = [re.sub(r'^\d+\s*-?\s*', '', o.strip()) for o in raw_list if o.strip()]
                        opp_acc_clean = '\n'.join(clean_list)
                    else:
                        opp_acc_clean = ''

                    # ONE-LINE FOR REF/NARRATION USING \n
                    lref = str(line.get('lref') or '').strip().replace('\n', ' ')
                    lname = str(line.get('lname') or '').strip().replace('\n', ' ')
                    if lref and lname and lref != lname:
                        ref_narration = f"{lref}\n{lname}"
                    else:
                        ref_narration = lref or lname

                    # ---- DYNAMIC ROW HEIGHT LOGIC ----
                    # Count the newlines to force Excel to open the row height automatically
                    newlines_opp = opp_acc_clean.count('\n') if opp_acc_clean else 0
                    newlines_ref = ref_narration.count('\n') if ref_narration else 0
                    max_lines = max(newlines_opp, newlines_ref) + 1

                    if max_lines > 1:
                        # Default excel row height is 15. We multiply by number of lines + slight padding
                        sheet.set_row(row, 15 * max_lines)

                    # Format the date to DD/MM/YYYY
                    ldate = line.get('ldate', '')
                    if ldate and isinstance(ldate, (datetime.date, datetime.datetime)):
                        ldate = ldate.strftime('%d/%m/%Y')
                    elif isinstance(ldate, str) and '-' in ldate:
                        # Convert string 'YYYY-MM-DD' to 'DD/MM/YYYY'
                        try:
                            ldate = datetime.datetime.strptime(ldate, '%Y-%m-%d').strftime('%d/%m/%Y')
                        except:
                            pass

                    sheet.write(row, 0, ldate, cell_center)
                    sheet.write(row, 1, line.get('lcode', ''), cell_center)
                    sheet.write(row, 2, line.get('move_name', ''), cell_left)
                    sheet.write(row, 3, opp_acc_clean, cell_wrap)

                    debit = float(line.get('debit', 0.0))
                    credit = float(line.get('credit', 0.0))
                    balance = float(line.get('balance', 0.0))
                    total_debit += debit
                    total_credit += credit

                    sheet.write_number(row, 4, debit, num_fmt)
                    sheet.write_number(row, 5, credit, num_fmt)
                    sheet.write_number(row, 6, balance, balance_fmt)

                    sheet.write(row, 7, line.get('move_state', ''), cell_center)
                    sheet.write(row, 8, ref_narration, cell_wrap)

                    if has_bank_acc:
                        brs = line.get('brs_status_en', '') if is_bank_account else ''
                        sheet.write(row, 9, brs, cell_center)

                    row += 1

            # --- ACCOUNT TOTAL ROW ---
            sheet.merge_range(row, 0, row, 3, "Total:", init_bal_label_fmt)
            sheet.write_number(row, 4, total_debit, total_num_fmt)
            sheet.write_number(row, 5, total_credit, total_num_fmt)

            final_balance = account_data.get('balance', 0.0)
            sheet.write_number(row, 6, float(final_balance), init_bal_num_fmt)

            sheet.write(row, 7, '', init_bal_empty_fmt)
            sheet.write(row, 8, '', init_bal_empty_fmt)
            if has_bank_acc:
                sheet.write(row, 9, '', init_bal_empty_fmt)

            row += 2

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
