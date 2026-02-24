# -*- coding: utf-8 -*-
import io
import copy
from odoo import models, api, _
from odoo.tools.misc import xlsxwriter
import datetime


class KsDynamicFinancialXlsxAR(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def get_xlsx(self, ks_df_informations, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # =========================================================================================
        # SECTION 1: CA-GRADE EXPORT (EXCLUSIVELY FOR PROFIT AND LOSS)
        # =========================================================================================
        if self.display_name == 'Profit and Loss':
            sheet = workbook.add_worksheet('Profit & Loss')

            lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.with_context(
                no_format=True, print_mode=True, prefetch_fields=False
            ).ks_fetch_report_account_lines(ks_df_informations)

            current_company_id = ks_df_informations.get('company_id')
            ks_company_id = self.env['res.company'].sudo().browse(current_company_id)
            Account = self.env['account.account'].sudo()

            income_accounts = []
            expense_accounts = []
            processed_accounts = set()

            for line in lines:
                if line.get('ks_level') == 0:
                    continue
                if line.get('ks_level') == 4 and 'account' in line:
                    account_id = line.get('account')
                    if account_id in processed_accounts:
                        continue
                    processed_accounts.add(account_id)
                    account_rec = Account.browse(account_id)

                    if account_rec.company_id.id != current_company_id:
                        continue

                    acc = dict(line)
                    acc['parent'] = False
                    acc['ks_level'] = 1
                    acc['list_len'] = [0]
                    acc['main_group'] = dict(account_rec._fields['main_group'].selection).get(
                        account_rec.main_group) or '' if account_rec.main_group else ''
                    acc['sub_group'] = dict(account_rec._fields['account_type'].selection).get(
                        account_rec.account_type) or '' if account_rec.account_type else ''
                    acc['sub_sub_group'] = account_rec.sub_sub_group_id.name if account_rec.sub_sub_group_id else ''

                    deb = float(acc.get('debit', 0.0))
                    cre = float(acc.get('credit', 0.0))

                    # Native Balance for accurate Dr/Cr formatting
                    acc['balance'] = round(deb - cre, 2)

                    if account_rec.internal_group == 'income':
                        income_accounts.append(acc)
                    elif account_rec.internal_group == 'expense':
                        expense_accounts.append(acc)

            # --- CALCULATE PURE MAGNITUDES FOR EXCEL ---
            tot_inc_raw = sum(a.get('balance', 0.0) for a in income_accounts)
            tot_exp_raw = sum(a.get('balance', 0.0) for a in expense_accounts)

            tot_inc_display = abs(tot_inc_raw)
            tot_exp_display = abs(tot_exp_raw)

            net_value = tot_inc_display - tot_exp_display
            net_label = 'Net Profit' if net_value >= 0 else 'Net Loss'
            display_net = abs(net_value)

            tot_inc_deb = sum(a.get('debit', 0.0) for a in income_accounts)
            tot_inc_cre = sum(a.get('credit', 0.0) for a in income_accounts)
            tot_exp_deb = sum(a.get('debit', 0.0) for a in expense_accounts)
            tot_exp_cre = sum(a.get('credit', 0.0) for a in expense_accounts)

            new_report_lines = []
            new_report_lines.append({
                'ks_name': 'Income', 'ks_level': 0, 'parent': False, 'list_len': [],
                'balance': round(tot_inc_deb - tot_inc_cre, 2),
                'debit': tot_inc_deb, 'credit': tot_inc_cre,
            })
            new_report_lines.extend(income_accounts)

            new_report_lines.append({
                'ks_name': 'Expenses', 'ks_level': 0, 'parent': False, 'list_len': [],
                'balance': round(tot_exp_deb - tot_exp_cre, 2),
                'debit': tot_exp_deb, 'credit': tot_exp_cre,
            })
            new_report_lines.extend(expense_accounts)

            new_report_lines.append({'is_spacer': True})
            new_report_lines.append(
                {'ks_name': 'Total Income', 'ks_level': 0, 'parent': False, 'list_len': [], 'balance': tot_inc_display,
                 'debit': '', 'credit': '', 'is_net_section': True})
            new_report_lines.append({'ks_name': 'Total Expenses', 'ks_level': 0, 'parent': False, 'list_len': [],
                                     'balance': tot_exp_display, 'debit': '', 'credit': '', 'is_net_section': True})
            new_report_lines.append(
                {'ks_name': net_label, 'ks_level': 0, 'parent': False, 'list_len': [], 'balance': display_net,
                 'debit': '', 'credit': '', 'is_net_section': True})

            # --- PROFESSIONAL CA EXCEL FORMATTING ---
            curr_sym = ks_company_id.currency_id.symbol or '₹'

            title_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14, 'font_name': 'Arial'})
            subtitle_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_name': 'Arial',
                 'color': '#555555'})
            header_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_name': 'Arial',
                 'bg_color': '#2d5b8c', 'font_color': '#ffffff', 'border': 1})

            str_fmt = workbook.add_format(
                {'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'left', 'valign': 'vcenter',
                 'text_wrap': True})
            bold_str = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'left', 'valign': 'vcenter',
                 'bg_color': '#f2f2f2'})

            # Custom Number Format 1: Debit & Credit Columns (NO CURRENCY SYMBOL, Just Numbers)
            c_num_dr_cr = workbook.add_format(
                {'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right', 'valign': 'vcenter'})
            c_num_dr_cr.set_num_format('#,##0.00')
            c_bold_dr_cr = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right',
                 'valign': 'vcenter', 'bg_color': '#f2f2f2'})
            c_bold_dr_cr.set_num_format('#,##0.00')

            # Custom Number Format 2: Balance Columns (Dynamic Dr/Cr formatting WITH Symbol)
            c_num_bal = workbook.add_format(
                {'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right', 'valign': 'vcenter'})
            c_num_bal.set_num_format(f'"{curr_sym}" #,##0.00 "Dr";"{curr_sym}" #,##0.00 "Cr";"{curr_sym}" 0.00')
            c_bold_bal = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right',
                 'valign': 'vcenter', 'bg_color': '#f2f2f2'})
            c_bold_bal.set_num_format(f'"{curr_sym}" #,##0.00 "Dr";"{curr_sym}" #,##0.00 "Cr";"{curr_sym}" 0.00')

            # Custom Number Format 3: Net Section (Only currency, always absolute)
            c_bold_net = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right',
                 'valign': 'vcenter', 'bg_color': '#f2f2f2'})
            c_bold_net.set_num_format(f'"{curr_sym}" #,##0.00')

            # Expanded Column Widths
            sheet.set_column(0, 0, 45)  # Account Name
            sheet.set_column(1, 3, 18)  # Dr, Cr, Balance
            sheet.set_column(4, 4, 20)  # Main Group
            sheet.set_column(5, 5, 25)  # Sub Group
            sheet.set_column(6, 6, 45)  # Sub Sub Group (Extra Wide)

            sheet.freeze_panes(5, 1)

            # Clean Single-Row Date Formatting
            lang = self.env.user.lang
            lang_id_rec = self.env['res.lang'].search([('code', '=', lang)], limit=1)
            date_fmt_str = lang_id_rec.date_format.replace('/', '-') if lang_id_rec else '%Y-%m-%d'
            ks_start = ks_df_informations['date'].get('ks_start_date')
            ks_end = ks_df_informations['date'].get('ks_end_date')
            start_dt = datetime.datetime.strptime(ks_start, '%Y-%m-%d').date().strftime(
                date_fmt_str) if ks_start else ''
            end_dt = datetime.datetime.strptime(ks_end, '%Y-%m-%d').date().strftime(date_fmt_str) if ks_end else ''

            if ks_df_informations['date']['ks_process'] == 'range':
                date_string = f"From: {start_dt}   To: {end_dt}"
            else:
                date_string = f"As of: {end_dt}"

            # --- WRITE TOP HEADERS ---
            sheet.merge_range(0, 0, 0, 6, ks_company_id.name.upper(), title_fmt)
            sheet.merge_range(1, 0, 1, 6, self.display_name.upper(), subtitle_fmt)
            sheet.merge_range(2, 0, 2, 6, date_string, subtitle_fmt)

            # --- WRITE TABLE HEADERS ---
            headers = ['Account Name', 'Debit', 'Credit', 'Balance', 'Main Group', 'Sub Group', 'Sub Sub Group']
            for col, head in enumerate(headers):
                sheet.write_string(4, col, head, header_fmt)

            # --- WRITE DATA LINES ---
            row_pos = 5
            for a in new_report_lines:
                # Blank Spacer Row
                if a.get('is_spacer'):
                    for col in range(7):
                        sheet.write_string(row_pos, col, '', str_fmt)
                    row_pos += 1
                    continue

                is_main_row = not bool(a.get('account'))
                is_net_section = a.get('is_net_section', False)

                # Select exact style per cell type
                c_str_style = bold_str if is_main_row else str_fmt
                c_drcr_style = c_bold_dr_cr if is_main_row else c_num_dr_cr

                if is_net_section:
                    c_bal_style = c_bold_net
                else:
                    c_bal_style = c_bold_bal if is_main_row else c_num_bal

                # 1. Name
                name = a.get('ks_name', '')
                indent = '   ' * len(a.get('list_len', []))
                sheet.write_string(row_pos, 0, indent + name, c_str_style)

                # 2. Debit
                if a.get('debit', '') != '':
                    sheet.write_number(row_pos, 1, float(a.get('debit', 0.0)), c_drcr_style)
                else:
                    sheet.write_string(row_pos, 1, '', c_str_style)

                # 3. Credit
                if a.get('credit', '') != '':
                    sheet.write_number(row_pos, 2, float(a.get('credit', 0.0)), c_drcr_style)
                else:
                    sheet.write_string(row_pos, 2, '', c_str_style)

                # 4. Balance (Applying the custom Dr/Cr mask logic)
                if a.get('balance', '') != '':
                    val = float(a.get('balance', 0.0))
                    if is_net_section:
                        val = abs(val)  # Forces absolute value for the net mask
                    sheet.write_number(row_pos, 3, val, c_bal_style)
                else:
                    sheet.write_string(row_pos, 3, '', c_str_style)

                # 5-7. Groups
                sheet.write_string(row_pos, 4, a.get('main_group', ''), c_str_style)
                sheet.write_string(row_pos, 5, a.get('sub_group', ''), c_str_style)
                sheet.write_string(row_pos, 6, a.get('sub_sub_group', ''), c_str_style)
                row_pos += 1

            workbook.close()
            output.seek(0)
            return output.read()

        # =========================================================================================
        # SECTION 2: CA-GRADE EXPORT (EXCLUSIVELY FOR BALANCE SHEET)
        # =========================================================================================
        elif self.display_name == 'Balance Sheet':
            sheet = workbook.add_worksheet('Balance Sheet')

            lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.with_context(
                no_format=True, print_mode=True, prefetch_fields=False
            ).ks_fetch_report_account_lines(ks_df_informations)

            current_company_id = ks_df_informations.get('company_id')
            ks_company_id = self.env['res.company'].sudo().browse(current_company_id)
            Account = self.env['account.account'].sudo()

            # EXACT UI CLONE FLATTENING
            bs_grouped_accounts = {}
            processed_accounts = set()

            for line in lines:
                if line.get('ks_level') == 0:
                    continue

                if 'account' in line and line.get('account'):
                    account_id = line.get('account')
                    if account_id in processed_accounts:
                        continue
                    processed_accounts.add(account_id)

                    account_rec = Account.browse(account_id)

                    if account_rec.company_id.id != current_company_id:
                        continue

                    if account_rec.internal_group in ('income', 'expense'):
                        continue

                    acc = dict(line)
                    acc['parent'] = False
                    acc['ks_level'] = 1
                    acc['list_len'] = [0]
                    acc['is_bs'] = True

                    acc['main_group'] = dict(account_rec._fields['main_group'].selection).get(
                        account_rec.main_group) or '' if account_rec.main_group else ''
                    acc['sub_group'] = dict(account_rec._fields['account_type'].selection).get(
                        account_rec.account_type) or '' if account_rec.account_type else ''
                    acc['sub_sub_group'] = account_rec.sub_sub_group_id.name if account_rec.sub_sub_group_id else ''

                    m_group_key = account_rec.main_group or 'OTHER'
                    if m_group_key not in bs_grouped_accounts:
                        bs_grouped_accounts[m_group_key] = []

                    bs_grouped_accounts[m_group_key].append(acc)

            new_report_lines = []

            def get_sort_weight(m_group):
                m = (m_group or '').lower()
                if 'asset' in m: return 1
                if 'liabilit' in m: return 2
                if 'equity' in m: return 3
                return 4

            sorted_main_groups = sorted(bs_grouped_accounts.keys(), key=lambda x: get_sort_weight(x))

            for m_group_key in sorted_main_groups:
                accounts_in_group = bs_grouped_accounts[m_group_key]

                if accounts_in_group:
                    sample_acc = Account.browse(accounts_in_group[0]['account'])
                    m_group_label = dict(sample_acc._fields['main_group'].selection).get(
                        m_group_key) or m_group_key if m_group_key != 'OTHER' else 'Other'
                else:
                    m_group_label = m_group_key

                tot_deb = round(sum(a.get('debit', 0.0) for a in accounts_in_group), 2)
                tot_cre = round(sum(a.get('credit', 0.0) for a in accounts_in_group), 2)
                tot_bal = round(sum(a.get('balance', 0.0) for a in accounts_in_group), 2)
                tot_init = round(sum(a.get('initial_balance', 0.0) for a in accounts_in_group), 2)

                new_report_lines.append({
                    'ks_name': str(m_group_label).upper(),
                    'ks_level': 0,
                    'balance': tot_bal,
                    'initial_balance': tot_init,
                    'debit': tot_deb,
                    'credit': tot_cre,
                    'is_bs': True
                })
                new_report_lines.extend(accounts_in_group)

            # PROFESSIONAL CA EXCEL FORMATTING FOR BALANCE SHEET
            curr_sym = ks_company_id.currency_id.symbol or '₹'

            title_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 14, 'font_name': 'Arial'})
            subtitle_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_name': 'Arial',
                 'color': '#555555'})
            header_fmt = workbook.add_format(
                {'bold': True, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_name': 'Arial',
                 'bg_color': '#2d5b8c', 'font_color': '#ffffff', 'border': 1})

            str_fmt = workbook.add_format(
                {'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'left', 'valign': 'vcenter',
                 'text_wrap': True})
            bold_str = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'left', 'valign': 'vcenter',
                 'bg_color': '#f2f2f2'})

            c_num_dr_cr = workbook.add_format(
                {'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right', 'valign': 'vcenter'})
            c_num_dr_cr.set_num_format('#,##0.00')
            c_bold_dr_cr = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right',
                 'valign': 'vcenter', 'bg_color': '#f2f2f2'})
            c_bold_dr_cr.set_num_format('#,##0.00')

            c_num_bal = workbook.add_format(
                {'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right', 'valign': 'vcenter'})
            c_num_bal.set_num_format(f'"{curr_sym}" #,##0.00 "Dr";"{curr_sym}" #,##0.00 "Cr";"{curr_sym}" 0.00')
            c_bold_bal = workbook.add_format(
                {'bold': True, 'font_size': 10, 'font_name': 'Arial', 'border': 1, 'align': 'right',
                 'valign': 'vcenter', 'bg_color': '#f2f2f2'})
            c_bold_bal.set_num_format(f'"{curr_sym}" #,##0.00 "Dr";"{curr_sym}" #,##0.00 "Cr";"{curr_sym}" 0.00')

            # Includes Initial Balance width
            sheet.set_column(0, 0, 45)
            sheet.set_column(1, 4, 18)
            sheet.set_column(5, 5, 20)
            sheet.set_column(6, 6, 25)
            sheet.set_column(7, 7, 35)
            sheet.freeze_panes(5, 1)

            lang = self.env.user.lang
            lang_id_rec = self.env['res.lang'].search([('code', '=', lang)], limit=1)
            date_fmt_str = lang_id_rec.date_format.replace('/', '-') if lang_id_rec else '%Y-%m-%d'
            ks_start = ks_df_informations['date'].get('ks_start_date')
            ks_end = ks_df_informations['date'].get('ks_end_date')
            start_dt = datetime.datetime.strptime(ks_start, '%Y-%m-%d').date().strftime(
                date_fmt_str) if ks_start else ''
            end_dt = datetime.datetime.strptime(ks_end, '%Y-%m-%d').date().strftime(date_fmt_str) if ks_end else ''

            if ks_df_informations['date']['ks_process'] == 'range':
                date_string = f"From: {start_dt}   To: {end_dt}"
            else:
                date_string = f"As of: {end_dt}"

            sheet.merge_range(0, 0, 0, 7, ks_company_id.name.upper(), title_fmt)
            sheet.merge_range(1, 0, 1, 7, self.display_name.upper(), subtitle_fmt)
            sheet.merge_range(2, 0, 2, 7, date_string, subtitle_fmt)

            headers = ['Account Details', 'Initial Balance', 'Debit', 'Credit', 'Balance', 'Main Group', 'Sub Group',
                       'Sub Sub Group']
            for col, head in enumerate(headers):
                sheet.write_string(4, col, head, header_fmt)

            row_pos = 5
            for a in new_report_lines:
                is_main_row = not bool(a.get('account'))

                c_str_style = bold_str if is_main_row else str_fmt
                c_drcr_style = c_bold_dr_cr if is_main_row else c_num_dr_cr
                c_bal_style = c_bold_bal if is_main_row else c_num_bal

                # 1. Name
                name = a.get('ks_name', '')
                indent = '   ' * len(a.get('list_len', []))
                sheet.write_string(row_pos, 0, indent + name, c_str_style)

                # 2. Initial Balance
                if a.get('initial_balance', '') != '':
                    sheet.write_number(row_pos, 1, float(a.get('initial_balance', 0.0)), c_bal_style)
                else:
                    sheet.write_string(row_pos, 1, '', c_str_style)

                # 3. Debit
                if a.get('debit', '') != '':
                    sheet.write_number(row_pos, 2, float(a.get('debit', 0.0)), c_drcr_style)
                else:
                    sheet.write_string(row_pos, 2, '', c_str_style)

                # 4. Credit
                if a.get('credit', '') != '':
                    sheet.write_number(row_pos, 3, float(a.get('credit', 0.0)), c_drcr_style)
                else:
                    sheet.write_string(row_pos, 3, '', c_str_style)

                # 5. Balance
                if a.get('balance', '') != '':
                    sheet.write_number(row_pos, 4, float(a.get('balance', 0.0)), c_bal_style)
                else:
                    sheet.write_string(row_pos, 4, '', c_str_style)

                # 6-8. Groups
                sheet.write_string(row_pos, 5, a.get('main_group', ''), c_str_style)
                sheet.write_string(row_pos, 6, a.get('sub_group', ''), c_str_style)
                sheet.write_string(row_pos, 7, a.get('sub_sub_group', ''), c_str_style)

                row_pos += 1

            workbook.close()
            output.seek(0)
            return output.read()

        # =========================================================================================
        # SECTION 3: EXISTING FEATURES (EXECUTIVE SUMMARY AND OTHERS)
        # =========================================================================================
        else:
            sheet = workbook.add_worksheet(self.display_name[:31])

            if self.display_name != "Executive Summary":
                lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.with_context(
                    no_format=True, print_mode=True, prefetch_fields=False
                ).ks_fetch_report_account_lines(ks_df_informations)
            else:
                lines = self.ks_process_executive_summary(ks_df_informations)

            ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

            sheet.freeze_panes(4, 1)
            row_pos = 0
            row_pos_2 = 0
            format_title = workbook.add_format({
                'bold': True, 'align': 'center', 'font_size': 12, 'border': False, 'font': 'Arial',
            })
            format_header = workbook.add_format({
                'bold': True, 'font_size': 10, 'align': 'center', 'font': 'Arial', 'bottom': False
            })
            content_header = workbook.add_format({
                'bold': False, 'font_size': 10, 'align': 'center', 'font': 'Arial',
            })
            content_header_date = workbook.add_format({
                'bold': False, 'font_size': 10, 'align': 'center', 'font': 'Arial',
            })
            line_header = workbook.add_format({
                'bold': False, 'font_size': 10, 'align': 'right', 'font': 'Arial', 'bottom': True
            })
            line_header.set_num_format('#,##0.' + '0' * ks_company_id.currency_id.decimal_places or 2)
            line_header_bold = workbook.add_format({
                'bold': True, 'font_size': 10, 'align': 'right', 'font': 'Arial', 'bottom': True
            })
            line_header_bold.set_num_format('#,##0.' + '0' * ks_company_id.currency_id.decimal_places or 2)
            line_header_string = workbook.add_format({
                'bold': False, 'font_size': 10, 'align': 'left', 'font': 'Arial', 'bottom': True
            })
            line_header_string_bold = workbook.add_format({
                'bold': True, 'font_size': 10, 'align': 'left', 'font': 'Arial', 'bottom': True
            })

            lang = self.env.user.lang
            lang_id_str = self.env['res.lang'].search([('code', '=', lang)])['date_format'].replace('/', '-')
            ks_new_start_date = (datetime.datetime.strptime(
                ks_df_informations['date'].get('ks_start_date'), '%Y-%m-%d').date()).strftime(lang_id_str)
            ks_new_end_date = (datetime.datetime.strptime(
                ks_df_informations['date'].get('ks_end_date'), '%Y-%m-%d').date()).strftime(lang_id_str)

            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                ks_new_start_comp_date = (datetime.datetime.strptime(
                    ks_df_informations['ks_differ'].get('ks_intervals')[-1]['ks_start_date'],
                    '%Y-%m-%d').date()).strftime(
                    lang_id_str)
                ks_new_end_comp_date = (datetime.datetime.strptime(
                    ks_df_informations['ks_differ'].get('ks_intervals')[-1]['ks_end_date'],
                    '%Y-%m-%d').date()).strftime(
                    lang_id_str)

            if self.display_name != 'Executive Summary':
                if not ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                    if ks_df_informations['date']['ks_process'] == 'range':
                        sheet.write_string(row_pos_2, 0, _('Date from'), format_header)
                        if ks_df_informations['date'].get('ks_start_date'):
                            sheet.write_string(row_pos_2, 1, ks_new_start_date, content_header_date)
                        row_pos_2 += 1
                        sheet.write_string(row_pos_2, 0, _('Date to'), format_header)
                        if ks_df_informations['date'].get('ks_end_date'):
                            sheet.write_string(row_pos_2, 1, ks_new_end_date, content_header_date)
                    else:
                        sheet.write_string(row_pos_2, 0, _('As of Date'), format_header)
                        if ks_df_informations['date'].get('ks_end_date'):
                            sheet.write_string(row_pos_2, 1, ks_new_end_date, content_header_date)

                    row_pos_2 += 1
                    if ks_df_informations.get('analytic_accounts'):
                        sheet.write_string(row_pos_2, 0, _('Analytic Accounts'), format_header)
                        a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_account_names'])
                        sheet.write_string(row_pos_2, 1, a_list, content_header)
                    row_pos_2 += 1
                    if ks_df_informations.get('analytic_tags'):
                        sheet.write_string(row_pos_2, 0, _('Tags'), format_header)
                        a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_tag_names'])
                        sheet.write_string(row_pos_2, 1, a_list, content_header)

                if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                    sheet.write_string(row_pos_2, 0, _('Comparison Date from'), format_header)
                    sheet.write_string(row_pos_2, 1, ks_new_start_comp_date, content_header_date)
                    row_pos_2 += 1
                    sheet.write_string(row_pos_2, 0, _('Comparison Date to'), format_header)
                    sheet.write_string(row_pos_2, 1, ks_new_end_comp_date, content_header_date)

                row_pos_2 += 0
                sheet.write_string(row_pos_2 - 3, 2, _('Journals All'), format_header)
                j_list = ', '.join(
                    journal.get('code') or '' for journal in ks_df_informations['journals'] if journal.get('selected'))
                sheet.write_string(row_pos_2 - 2, 2, j_list, content_header)

                row_pos += 3
                if ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:
                    sheet.set_column(0, 0, 90)
                    sheet.set_column(1, 1, 15)
                    sheet.set_column(2, 3, 15)
                    sheet.set_column(3, 3, 15)

                    sheet.write_string(row_pos, 0, _('Name'), format_header)
                    sheet.write_string(row_pos, 1, _('Debit'), format_header)
                    sheet.write_string(row_pos, 2, _('Credit'), format_header)
                    sheet.write_string(row_pos, 3, _('Balance'), format_header)

                    for a in lines:
                        row_pos += 1
                        if a.get('ks_level') == 3:
                            tmp_style_str = line_header_string_bold
                            tmp_style_num = line_header_bold
                        elif a.get('account', False):
                            tmp_style_str = line_header_string
                            tmp_style_num = line_header
                        else:
                            tmp_style_str = line_header_string_bold
                            tmp_style_num = line_header_bold

                        sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name', ''),
                                           tmp_style_str)
                        sheet.write_number(row_pos, 1, float(a.get('debit', 0.0)), tmp_style_num)
                        sheet.write_number(row_pos, 2, float(a.get('credit', 0.0)), tmp_style_num)
                        sheet.write_number(row_pos, 3, float(a.get('balance', 0.0)), tmp_style_num)

                if not ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:
                    sheet.set_column(0, 0, 105)
                    sheet.set_column(1, 1, 15)
                    sheet.set_column(2, 2, 15)
                    sheet.write_string(row_pos, 0, _('Name'), format_header)
                    col_pos = 0

                    if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                        for i in lines[0].get('balance_cmp', {}):
                            sheet.write_string(row_pos, col_pos + 1, i.split('comp_bal_')[1], format_header)
                            sheet.write_string(row_pos, (col_pos + 1) + 1, _('Balance'), format_header)
                            col_pos += 1
                    else:
                        sheet.write_string(row_pos, 1, _('Balance'), format_header)

                    for a in lines:
                        if a.get('ks_level') == 2:
                            row_pos += 1
                        row_pos += 1
                        if a.get('account', False):
                            tmp_style_str = line_header_string
                            tmp_style_num = line_header
                        else:
                            tmp_style_str = line_header_string_bold
                            tmp_style_num = line_header_bold

                        sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name', ''),
                                           tmp_style_str)
                        if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                            col_pos = 0
                            for i in a.get('balance_cmp', {}):
                                sheet.write_number(row_pos, col_pos + 1, float(a['balance_cmp'][i]), tmp_style_num)
                                sheet.write_number(row_pos, (col_pos + 1) + 1, float(a.get('balance', 0.0)),
                                                   tmp_style_num)
                                col_pos += 1
                        else:
                            sheet.write_number(row_pos, 1, float(a.get('balance', 0.0)), tmp_style_num)

            workbook.close()
            output.seek(0)
            return output.read()