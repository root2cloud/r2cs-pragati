# -*- coding: utf-8 -*-
import io
from odoo import models, api, _
from odoo.tools.misc import xlsxwriter
import datetime


class KsDynamicFinancialXlsxAR(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def get_xlsx(self, ks_df_informations, response=None):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(self.display_name[:31])
        if self.display_name != "Executive Summary":
            lines, ks_initial_balance, ks_current_balance, ks_ending_balance = self.with_context(no_format=True,
                                                                                                 print_mode=True,
                                                                                                 prefetch_fields=False).ks_fetch_report_account_lines(
                ks_df_informations)
            if self.display_name == 'Profit and Loss':
                info = {'ks_report_lines': lines}

                import copy

                Account = self.env['account.account']

                for line in info.get('ks_report_lines', []):
                    if 'account' in line:
                        account_id = line['account']
                        account_rec = Account.browse(account_id)

                        sub_group = account_rec.sub_sub_group_id
                        line['sub_type_id'] = sub_group.id if sub_group else False
                        line['sub_type_name'] = sub_group.name if sub_group else ""


                new_id_counter = 500000
                grouped_sub_types = {}
                lines_to_remove = set()

                OTHER_SUB_TYPE_ID = -1
                OTHER_SUB_TYPE_NAME = "OTHER"
                processed_accounts = set()

                for line in info.get('ks_report_lines', []):

                    if line.get('ks_level') != 4:
                        continue

                    account_id = line.get('account')

                    if account_id in processed_accounts:
                        continue

                    processed_accounts.add(account_id)

                    parent_level_2_id = line.get('parent')

                    # Determine subgroup (real or OTHER)
                    if line.get('sub_type_id'):
                        sub_type_id = line['sub_type_id']
                        sub_type_name = line['sub_type_name']
                    else:
                        sub_type_id = OTHER_SUB_TYPE_ID
                        sub_type_name = OTHER_SUB_TYPE_NAME

                    lines_to_remove.add(id(line))

                    if parent_level_2_id not in grouped_sub_types:
                        grouped_sub_types[parent_level_2_id] = {}

                    if sub_type_id not in grouped_sub_types[parent_level_2_id]:
                        grouped_sub_types[parent_level_2_id][sub_type_id] = {
                            'sub_type_name': sub_type_name,
                            'accounts': [],
                            'balance': 0.0,
                            'debit': 0.0,
                            'credit': 0.0,
                            'currency_id': line['company_currency_id'],
                        }

                    group_data = grouped_sub_types[parent_level_2_id][sub_type_id]

                    account_copy = copy.deepcopy(line)
                    group_data['accounts'].append(account_copy)

                    group_data['balance'] += line.get('balance', 0.0)
                    group_data['debit'] += line.get('debit', 0.0)
                    group_data['credit'] += line.get('credit', 0.0)


                original_lines = info.get('ks_report_lines', [])
                new_report_lines = []

                for line in original_lines:

                    if line.get('ks_level') == 4 and id(line) in lines_to_remove:
                        continue

                    new_report_lines.append(line)

                    if line.get('ks_level') == 2 and line.get('self_id') in grouped_sub_types:
                        parent_level_2_id = line['self_id']

                        for sub_type_id in sorted(grouped_sub_types[parent_level_2_id].keys()):
                            group_data = grouped_sub_types[parent_level_2_id][sub_type_id]

                            new_level_3_id = new_id_counter
                            new_id_counter += 1

                            level_3_line = {
                                'ks_name': group_data['sub_type_name'],
                                'balance': group_data['balance'],
                                'parent': parent_level_2_id,
                                'self_id': new_level_3_id,
                                'ks_df_report_account_type': 'report',
                                'style_type': 'sub_sub_total',
                                'precision': 2,
                                'symbol': '₹',
                                'position': 'before',
                                'list_len': [0, 1, 2],
                                'ks_level': 3,
                                'company_currency_id': group_data['currency_id'],
                                'account_type': 'sub_total',
                                'balance_cmp': {},
                                'debit': group_data.get('debit', 0.0),
                                'credit': group_data.get('credit', 0.0),
                                'sub_type_id': sub_type_id,
                            }

                            new_report_lines.append(level_3_line)

                            for acc in group_data['accounts']:
                                acc['parent'] = new_level_3_id
                                acc['list_len'] = [0, 1, 2, 3]
                                new_report_lines.append(acc)

                lines = new_report_lines

        else:
            lines = self.ks_process_executive_summary(ks_df_informations)
        if self.display_name == self.env.ref(
                'ks_dynamic_financial_report.ks_dynamic_financial_balancesheet').display_name:
            ks_bal_sum = 0
            for line in lines:

                # if line.get('ks_name') == 'LIABILITIES' or line.get('ks_name') == 'EQUITY':
                #     ks_bal_sum += line.get('balance', 0)

                if line.get('ks_name') == 'Previous Years Unallocated Earnings' and \
                        ks_df_informations['date']['ks_process'] == 'range':
                    ks_bal_sum -= line.get('balance', 0)
            lines[len(lines) - 1]['balance'] = ks_bal_sum

        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

        sheet.freeze_panes(4, 1)
        row_pos = 0
        row_pos_2 = 0
        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'border': False,
            'font': 'Arial',
        })
        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'bottom': False
        })
        content_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
        })
        content_header_date = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            # 'num_format': 'dd/mm/yyyy',
        })
        line_header = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': True
        })
        line_header.set_num_format(
            '#,##0.' + '0' * ks_company_id.currency_id.decimal_places or 2)
        line_header_bold = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'bottom': True
        })
        line_header_bold.set_num_format(
            '#,##0.' + '0' * ks_company_id.currency_id.decimal_places or 2)
        line_header_string = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': True
        })
        line_header_string_bold = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'bottom': True
        })
        # Date from
        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])['date_format'].replace('/', '-')
        ks_new_start_date = (datetime.datetime.strptime(
            ks_df_informations['date'].get('ks_start_date'), '%Y-%m-%d').date()).strftime(lang_id)
        ks_new_end_date = (datetime.datetime.strptime(
            ks_df_informations['date'].get('ks_end_date'), '%Y-%m-%d').date()).strftime(lang_id)
        if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
            ks_new_start_comp_date = (datetime.datetime.strptime(
                ks_df_informations['ks_differ'].get('ks_intervals')[-1]['ks_start_date'], '%Y-%m-%d').date()).strftime(
                lang_id)
            ks_new_end_comp_date = (datetime.datetime.strptime(
                ks_df_informations['ks_differ'].get('ks_intervals')[-1]['ks_end_date'], '%Y-%m-%d').date()).strftime(
                lang_id)
        if self.display_name != 'Executive Summary':
            if not ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                if ks_df_informations['date']['ks_process'] == 'range':
                    sheet.write_string(row_pos_2, 0, _('Date from'), format_header)
                    if ks_df_informations['date'].get('ks_start_date'):
                        sheet.write_string(row_pos_2, 1, ks_new_start_date,
                                           content_header_date)
                    row_pos_2 += 1
                    # Date to
                    sheet.write_string(row_pos_2, 0, _('Date to'), format_header)

                    if ks_df_informations['date'].get('ks_end_date'):
                        sheet.write_string(row_pos_2, 1, ks_new_end_date,
                                           content_header_date)
                else:
                    sheet.write_string(row_pos_2, 0, _('As of Date'), format_header)
                    if ks_df_informations['date'].get('ks_end_date'):
                        sheet.write_string(row_pos_2, 1, ks_new_end_date,
                                           content_header_date)
                # Accounts
                row_pos_2 += 1
                if ks_df_informations.get('analytic_accounts'):
                    sheet.write_string(row_pos_2, 0, _('Analytic Accounts'), format_header)
                    a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_account_names'])
                    sheet.write_string(row_pos_2, 1, a_list, content_header)
                # Tags
                row_pos_2 += 1
                if ks_df_informations.get('analytic_tags'):
                    sheet.write_string(row_pos_2, 0, _('Tags'), format_header)
                    a_list = ', '.join(lt or '' for lt in ks_df_informations['selected_analytic_tag_names'])
                    sheet.write_string(row_pos_2, 1, a_list, content_header)

            # Comparison filter
            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Comparison Date from'),
                                   format_header)


                sheet.write_string(row_pos_2, 1,
                                   ks_new_start_comp_date,
                                   content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Comparison Date to'),
                                   format_header)


                sheet.write_string(row_pos_2, 1,
                                   ks_new_end_comp_date,
                                   content_header_date)

            row_pos_2 += 0
            sheet.write_string(row_pos_2 - 3, 2, _('Journals All'),
                               format_header)
            j_list = ', '.join(
                journal.get('code') or '' for journal in ks_df_informations['journals'] if journal.get('selected'))
            sheet.write_string(row_pos_2 - 2, 2, j_list,
                               content_header)

            # Account
            row_pos_2 += 0
            # sheet.write_string(row_pos_2 - 3, 3, _('Account'), format_header)
            # j_list = ', '.join(
            #     journal.get('name') or '' for journal in ks_df_informations['account'] if journal.get('selected'))
            # sheet.write_string(row_pos_2 - 2, 3, j_list,
            #                    content_header)

            row_pos += 3
            if ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 90)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)

                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)
                sheet.write_string(row_pos, 1, _('Debit'),
                                   format_header)
                sheet.write_string(row_pos, 2, _('Credit'),
                                   format_header)
                sheet.write_string(row_pos, 3, _('Balance'),
                                   format_header)

                for a in lines:
                    row_pos += 1  # increment for every line

                    # Determine styles
                    if a.get('ks_level') == 3:  # Level 3 (sub-type total)
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    elif a.get('account', False):  # L4 accounts
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:  # L2 lines
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold

                    # Write data
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name', ''),
                                       tmp_style_str)

                    # Only write numbers if keys exist
                    if 'debit' in a:
                        sheet.write_number(row_pos, 1, float(a.get('debit', 0.0)), tmp_style_num)
                    if 'credit' in a:
                        sheet.write_number(row_pos, 2, float(a.get('credit', 0.0)), tmp_style_num)
                    if 'balance' in a:
                        sheet.write_number(row_pos, 3, float(a.get('balance', 0.0)), tmp_style_num)

            if not ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:
                sheet.set_column(0, 0, 105)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 2, 15)
                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)
                if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                    col_pos = 0
                    for i in lines[0]['balance_cmp']:
                        sheet.write_string(row_pos, col_pos + 1, i.split('comp_bal_')[1],
                                           format_header),
                        sheet.write_string(row_pos, (col_pos + 1) + 1, _('Balance'),
                                           format_header)
                        col_pos = col_pos + 1
                else:
                    sheet.write_string(row_pos, 1, _('Balance'),
                                       format_header)

                for a in lines:
                    if a['ks_level'] == 2:
                        row_pos += 1
                    row_pos += 1
                    if a.get('account', False):
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name'),
                                       tmp_style_str)
                    if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                        col_pos = 0
                        for i in a['balance_cmp']:
                            sheet.write_number(row_pos, col_pos + 1, float(a['balance_cmp'][i]), tmp_style_num)
                            sheet.write_number(row_pos, (col_pos + 1) + 1, float(a['balance']), tmp_style_num)
                            col_pos += 1
        else:
            if not ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                if ks_df_informations['date']['ks_process'] == 'range':
                    sheet.write_string(row_pos_2, 0, _('Date from'),
                                       format_header)
                    if ks_df_informations['date'].get('ks_start_date'):
                        sheet.write_string(row_pos_2, 1, ks_new_start_date,
                                           content_header_date)
                    row_pos_2 += 1
                    # Date to
                    sheet.write_string(row_pos_2, 0, _('Date to'),
                                       format_header)

                    if ks_df_informations['date'].get('ks_end_date'):
                        sheet.write_string(row_pos_2, 1, ks_new_end_date,
                                           content_header_date)
                else:
                    sheet.write_string(row_pos_2, 0, _('As of Date'),
                                       format_header)
                    if ks_df_informations['date'].get('ks_end_date'):
                        sheet.write_string(row_pos_2, 1, ks_new_end_date,
                                           content_header_date)
            if ks_df_informations['ks_diff_filter']['ks_diff_filter_enablity']:
                sheet.write_string(row_pos_2, 0, _('Comparison Date from'),
                                   format_header)


                sheet.write_string(row_pos_2, 1,
                                   ks_new_start_comp_date,
                                   content_header_date)
                row_pos_2 += 1
                # Date to
                sheet.write_string(row_pos_2, 0, _('Comparison Date to'),
                                   format_header)


                sheet.write_string(row_pos_2, 1,
                                   ks_new_end_comp_date,
                                   content_header_date)

            row_pos += 3
            # sheet.write_string(row_pos_2 - 3, 3, _('Account'), format_header)
            # j_list = ', '.join(
            #     journal.get('name') or '' for journal in ks_df_informations['account'] if journal.get('selected'))
            # sheet.write_string(row_pos_2 - 2, 3, j_list,
            #                    content_header)
            if ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 90)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)

                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)
                sheet.write_string(row_pos, 1, _('Debit'),
                                   format_header)
                sheet.write_string(row_pos, 2, _('Credit'),
                                   format_header)
                sheet.write_string(row_pos, 3, _('Balance'),
                                   format_header)

                for a in lines:
                    if a['ks_level'] == 2:
                        row_pos += 1
                    row_pos += 1
                    if a.get('account', False):
                        tmp_style_str = line_header_string
                        tmp_style_num = line_header
                    else:
                        tmp_style_str = line_header_string_bold
                        tmp_style_num = line_header_bold
                    sheet.write_string(row_pos, 0, '   ' * len(a.get('list_len', [])) + a.get('ks_name'),
                                       tmp_style_str)
                    if a.get('debit'):
                        for i in a.get('debit'):
                            sheet.write_number(row_pos, 1, float(a.get('debit', 0.0)[i]), tmp_style_num)
                    if a.get('credit'):
                        for i in a.get('credit'):
                            sheet.write_number(row_pos, 2, float(a.get('credit', 0.0)[i]), tmp_style_num)
                    if a.get('balance'):
                        for i in a.get('balance'):
                            sheet.write_number(row_pos, 3, float(a.get('balance', 0.0)[i]), tmp_style_num)

            if not ks_df_informations['ks_diff_filter']['ks_debit_credit_visibility']:

                sheet.set_column(0, 0, 50)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 3, 15)
                sheet.set_column(3, 3, 15)
                sheet.write_string(row_pos, 0, _('Name'),
                                   format_header)

                sheet.write_string(row_pos, 1, ks_df_informations['date']['ks_string'],
                                   format_header)
                ks_col = 2
                # for x in range(3):
                for i in ks_df_informations['ks_differ']['ks_intervals']:
                    sheet.write_string(row_pos, ks_col, i['ks_string'],
                                       format_header)
                    sheet.set_column(ks_col, ks_col, 20)
                    ks_col += 1

                ks_col_line = 0
                for line in lines:
                    sheet.write(row_pos + 1, 0, line['ks_name'],
                                line_header_string)
                    if line.get('balance'):
                        for ks in line.get('balance'):
                            sheet.write(row_pos + 1, ks_col_line + 1, line.get('balance')[ks],
                                        line_header)
                            ks_col_line += 1
                    ks_col_line = 0
                    row_pos += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
