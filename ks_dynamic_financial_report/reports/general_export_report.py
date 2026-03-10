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
        # 1. ULTIMATE INDIAN NUMBER FORMATS (FORCING EXCEL)
        # These 3-part conditions guarantee perfect Crores, Lakhs, Thousands, and Zeros.
        # ==========================================
        fmt_amount_pos = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'right', 'valign': 'top',
                                              'num_format': '[>=10000000]##\,##\,##\,##0.00;[>=100000]##\,##\,##0.00;##,##0.00'})
        fmt_amount_neg = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'right', 'valign': 'top',
                                              'num_format': '[>=10000000]-##\,##\,##\,##0.00;[>=100000]-##\,##\,##0.00;-##,##0.00'})

        fmt_total_pos = workbook.add_format(
            {'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a', 'align': 'right',
             'valign': 'vcenter',
             'num_format': '[>=10000000]"₹" ##\,##\,##\,##0.00;[>=100000]"₹" ##\,##\,##0.00;"₹" ##,##0.00'})
        fmt_total_neg = workbook.add_format(
            {'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a', 'align': 'right',
             'valign': 'vcenter',
             'num_format': '[>=10000000]"₹" -##\,##\,##\,##0.00;[>=100000]"₹" -##\,##\,##0.00;"₹" -##,##0.00'})

        fmt_bal_dr = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'right', 'valign': 'top',
                                          'num_format': '[>=10000000]"₹" ##\,##\,##\,##0.00 "Dr";[>=100000]"₹" ##\,##\,##0.00 "Dr";"₹" ##,##0.00 "Dr"'})
        fmt_bal_cr = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'right', 'valign': 'top',
                                          'num_format': '[>=10000000]"₹" ##\,##\,##\,##0.00 "Cr";[>=100000]"₹" ##\,##\,##0.00 "Cr";"₹" ##,##0.00 "Cr"'})

        fmt_init_bal_dr = workbook.add_format(
            {'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a', 'align': 'right',
             'valign': 'vcenter',
             'num_format': '[>=10000000]"₹" ##\,##\,##\,##0.00 "Dr";[>=100000]"₹" ##\,##\,##0.00 "Dr";"₹" ##,##0.00 "Dr"'})
        fmt_init_bal_cr = workbook.add_format(
            {'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a', 'align': 'right',
             'valign': 'vcenter',
             'num_format': '[>=10000000]"₹" ##\,##\,##\,##0.00 "Cr";[>=100000]"₹" ##\,##\,##0.00 "Cr";"₹" ##,##0.00 "Cr"'})

        # ==========================================
        # 2. STRICT ACCOUNTING EXCEL STYLES
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

        init_bal_label_fmt = workbook.add_format({
            'bg_color': '#f8f9fa', 'bold': True, 'border': 1, 'border_color': '#7a7a7a',
            'align': 'right', 'valign': 'vcenter'
        })

        init_bal_empty_fmt = workbook.add_format({
            'bg_color': '#f8f9fa', 'border': 1, 'border_color': '#7a7a7a',
        })

        cell_center = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'center', 'valign': 'top'})
        cell_left = workbook.add_format({'border': 1, 'border_color': '#7a7a7a', 'align': 'left', 'valign': 'top'})
        cell_wrap = workbook.add_format(
            {'border': 1, 'border_color': '#7a7a7a', 'align': 'left', 'valign': 'top', 'text_wrap': True})

        # ==========================================
        # 3. DETERMINE BRS COLUMN VISIBILITY
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
        # 4. SET EXPANDED COLUMNS FOR CLEAR VISIBILITY
        # ==========================================
        headers = ['Date', 'Journal', 'Voucher', 'Accounts', 'Debit', 'Credit', 'Balance', 'Status',
                   'Reference / Narration']
        if has_bank_acc:
            headers.append('BRS Status')

        total_cols = len(headers)

        sheet.set_column(0, 0, 12)  # Date
        sheet.set_column(1, 1, 28)  # Journal
        sheet.set_column(2, 2, 25)  # Voucher
        sheet.set_column(3, 3, 50)  # Accounts
        sheet.set_column(4, 5, 16)  # Debit, Credit
        sheet.set_column(6, 6, 20)  # Balance
        sheet.set_column(7, 7, 12)  # Status
        sheet.set_column(8, 8, 50)  # Ref/Narration
        if has_bank_acc:
            sheet.set_column(9, 9, 14)  # BRS

        # ==========================================
        # 5. PRINT REPORT TITLES (MERGED FOR CENTERING)
        # ==========================================
        row = 0
        sheet.merge_range(row, 0, row, total_cols - 1, ks_company_id.name, title_fmt)
        row += 1
        sheet.merge_range(row, 0, row, total_cols - 1, 'General Ledger', subtitle_fmt)
        row += 1

        if ks_df_informations.get('date') and ks_df_informations['date'].get('ks_start_date'):
            s_date = str(ks_df_informations['date'].get('ks_start_date'))
            e_date = str(ks_df_informations['date'].get('ks_end_date'))
            try:
                s_date = datetime.datetime.strptime(str(s_date)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                pass
            try:
                e_date = datetime.datetime.strptime(str(e_date)[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
            except Exception:
                pass
            date_str = f"Period: {s_date} To {e_date}"
            sheet.merge_range(row, 0, row, total_cols - 1, date_str, subtitle_fmt)
        row += 2

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_fmt)
        row += 1

        sheet.freeze_panes(row, 0)

        # ==========================================
        # 6. PRINT TRANSACTION DATA
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

            # Clean Account Header (UNMERGED)
            acc_header_text = f"Account: {actual_code} {actual_name}    [ Main Group: {main_grp}  |  Sub Group: {sub_grp}  |  Sub Sub Group: {ss_grp} ]"
            sheet.write(row, 0, acc_header_text, account_header_fmt)
            for col_idx in range(1, total_cols):
                sheet.write(row, col_idx, '', account_header_fmt)
            row += 1

            total_debit = 0.0
            total_credit = 0.0

            # ----------------------------------------------------
            # INITIAL BALANCE LOGIC
            # ----------------------------------------------------
            has_init_bal = False
            start_balance = 0.0

            for line in account_data.get('lines', []):
                if line.get('initial_bal'):
                    has_init_bal = True
                    start_balance = float(line.get('balance', 0.0))
                    break

            if not has_init_bal:
                start_balance = float(account_data.get('initial_balance', 0.0))

            # Print Initial Balance Row
            sheet.write(row, 0, '', init_bal_label_fmt)
            sheet.write(row, 1, '', init_bal_label_fmt)
            sheet.write(row, 2, '', init_bal_label_fmt)
            sheet.write(row, 3, "Initial Balance", init_bal_label_fmt)
            sheet.write(row, 4, '', init_bal_empty_fmt)
            sheet.write(row, 5, '', init_bal_empty_fmt)

            # Apply format based on Dr/Cr logic safely using absolute values
            if start_balance >= 0:
                sheet.write_number(row, 6, abs(start_balance), fmt_init_bal_dr)
            else:
                sheet.write_number(row, 6, abs(start_balance), fmt_init_bal_cr)

            sheet.write(row, 7, '', init_bal_empty_fmt)
            sheet.write(row, 8, '', init_bal_empty_fmt)
            if has_bank_acc:
                sheet.write(row, 9, '', init_bal_empty_fmt)
            row += 1

            # ----------------------------------------------------
            # TRANSACTION LINES
            # ----------------------------------------------------
            for line in account_data.get('lines', []):
                if line.get('initial_bal') or line.get('ending_bal'):
                    continue

                opp_acc_raw = str(line.get('corresponding_accounts') or '')
                if opp_acc_raw:
                    raw_list = opp_acc_raw.split(', ')
                    clean_list = [re.sub(r'^\d+\s*-?\s*', '', o.strip()) for o in raw_list if o.strip()]
                    opp_acc_clean = '\n'.join(clean_list)
                else:
                    opp_acc_clean = ''

                lref = str(line.get('lref') or '').strip().replace('\n', ' ')
                lname = str(line.get('lname') or '').strip().replace('\n', ' ')
                if lref and lname and lref != lname:
                    ref_narration = f"{lref}\n{lname}"
                else:
                    ref_narration = lref or lname

                newlines_opp = opp_acc_clean.count('\n') if opp_acc_clean else 0
                newlines_ref = ref_narration.count('\n') if ref_narration else 0
                max_lines = max(newlines_opp, newlines_ref) + 1

                if max_lines > 1:
                    sheet.set_row(row, 15 * max_lines)

                ldate = line.get('ldate', '')
                if ldate and isinstance(ldate, (datetime.date, datetime.datetime)):
                    ldate = ldate.strftime('%d/%m/%Y')
                elif isinstance(ldate, str) and '-' in ldate:
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

                if debit >= 0:
                    sheet.write_number(row, 4, abs(debit), fmt_amount_pos)
                else:
                    sheet.write_number(row, 4, abs(debit), fmt_amount_neg)

                if credit >= 0:
                    sheet.write_number(row, 5, abs(credit), fmt_amount_pos)
                else:
                    sheet.write_number(row, 5, abs(credit), fmt_amount_neg)

                if balance >= 0:
                    sheet.write_number(row, 6, abs(balance), fmt_bal_dr)
                else:
                    sheet.write_number(row, 6, abs(balance), fmt_bal_cr)

                sheet.write(row, 7, line.get('move_state', ''), cell_center)
                sheet.write(row, 8, ref_narration, cell_wrap)

                if has_bank_acc:
                    brs = line.get('brs_status_en', '') if is_bank_account else ''
                    sheet.write(row, 9, brs, cell_center)

                row += 1

            # ----------------------------------------------------
            # ACCOUNT TOTAL ROW (UNMERGED) & BUG FIX
            # ----------------------------------------------------
            sheet.write(row, 0, '', init_bal_label_fmt)
            sheet.write(row, 1, '', init_bal_label_fmt)
            sheet.write(row, 2, '', init_bal_label_fmt)
            sheet.write(row, 3, "Total:", init_bal_label_fmt)

            if total_debit >= 0:
                sheet.write_number(row, 4, abs(total_debit), fmt_total_pos)
            else:
                sheet.write_number(row, 4, abs(total_debit), fmt_total_neg)

            if total_credit >= 0:
                sheet.write_number(row, 5, abs(total_credit), fmt_total_pos)
            else:
                sheet.write_number(row, 5, abs(total_credit), fmt_total_neg)

            # FIX: Manually calculating the final balance to prevent the module's doubling bug
            calculated_final_balance = start_balance + total_debit - total_credit

            if calculated_final_balance >= 0:
                sheet.write_number(row, 6, abs(calculated_final_balance), fmt_init_bal_dr)
            else:
                sheet.write_number(row, 6, abs(calculated_final_balance), fmt_init_bal_cr)

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