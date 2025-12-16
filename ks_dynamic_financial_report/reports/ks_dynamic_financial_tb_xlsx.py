# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import xlsxwriter
import datetime
import io


class KsDynamicFinancialXlsxTB(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def ks_get_xlsx_trial_balance(self, ks_df_informations):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        row_pos = 0

        move_lines, retained, subtotal = self.ks_process_trial_balance(ks_df_informations)
        ks_company_id = self.env['res.company'].sudo().browse(ks_df_informations.get('company_id'))

        sheet = workbook.add_worksheet('Trial Balance')


        sheet.set_column(0, 0, 25)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 40)
        sheet.set_column(4, 4, 12)
        sheet.set_column(5, 10, 15)

        format_title = workbook.add_format({
            'bold': True, 'align': 'center',
            'font_size': 12, 'bg_color': '#4472C4',
            'font_color': 'white'
        })

        format_company = workbook.add_format({
            'bold': True, 'align': 'center',
            'font_size': 11
        })

        format_date_range = workbook.add_format({
            'bold': True, 'align': 'center',
            'italic': True
        })

        format_header = workbook.add_format({
            'bold': True, 'align': 'center',
            'bg_color': '#4472C4', 'font_color': 'white',
            'border': 1
        })

        format_subheader = workbook.add_format({
            'bold': True, 'align': 'center',
            'bg_color': '#4472C4', 'font_color': 'white',
            'border': 1
        })

        fmt_left = workbook.add_format({'border': 1, 'align': 'left'})
        fmt_center = workbook.add_format({'border': 1, 'align': 'center'})
        fmt_right = workbook.add_format({'border': 1, 'align': 'right'})
        fmt_right.set_num_format('#,##0.00')

        total_left = workbook.add_format({
            'bold': True, 'align': 'left',
            'border': 1, 'bg_color': '#FFD966'
        })
        total_right = workbook.add_format({
            'bold': True, 'align': 'right',
            'border': 1, 'bg_color': '#FFD966'
        })
        total_right.set_num_format('#,##0.00')


        start_date = ks_df_informations['date']['ks_start_date']
        end_date = ks_df_informations['date']['ks_end_date']
        start_fmt = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        end_fmt = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        date_range_text = f"[Custom Range ({start_fmt} to {end_fmt})]"


        sheet.merge_range(row_pos, 0, row_pos, 10, ks_company_id.name.upper(), format_company)
        row_pos += 1
        sheet.merge_range(row_pos, 0, row_pos, 10, "TRIAL BALANCE", format_title)
        row_pos += 1
        sheet.merge_range(row_pos, 0, row_pos, 10, date_range_text, format_date_range)
        row_pos += 2

        sheet.write(row_pos, 0, "Main Group", format_header)
        sheet.write(row_pos, 1, "Account Type", format_header)
        sheet.write(row_pos, 2, "Sub Type", format_header)
        sheet.write(row_pos, 3, "Particulars", format_header)
        sheet.write(row_pos, 4, "Code", format_header)

        sheet.merge_range(row_pos, 5, row_pos, 6, "Opening Balance", format_header)
        sheet.merge_range(row_pos, 7, row_pos, 8, "Transaction", format_header)
        sheet.merge_range(row_pos, 9, row_pos, 10, "Closing Balance", format_header)
        row_pos += 1

        # Sub headers
        for col in range(5):
            sheet.write(row_pos, col, "", format_subheader)

        sheet.write(row_pos, 5, "Dr (Op)", format_subheader)
        sheet.write(row_pos, 6, "Cr (Op)", format_subheader)
        sheet.write(row_pos, 7, "Debits", format_subheader)
        sheet.write(row_pos, 8, "Credits", format_subheader)
        sheet.write(row_pos, 9, "Dr (YTD)", format_subheader)
        sheet.write(row_pos, 10, "Cr (YTD)", format_subheader)
        row_pos += 1


        hierarchy = {}
        for account_code,line in move_lines.items():
            main = line.get("main_type") or "Others"
            acc = line.get("account_type") or "Others"
            sub = line.get("sub_type") or "Others"

            hierarchy.setdefault(main, {})
            hierarchy[main].setdefault(acc, {})
            hierarchy[main][acc].setdefault(sub, [])
            hierarchy[main][acc][sub].append(line)

        def sum_group(lines):
            return (
                sum(l["initial_debit"] for l in lines),
                sum(l["initial_credit"] for l in lines),
                sum(l["debit"] for l in lines),
                sum(l["credit"] for l in lines),
                sum(l["ending_debit"] for l in lines),
                sum(l["ending_credit"] for l in lines),
            )


        for main, acc_types in hierarchy.items():

            main_lines = [l for a in acc_types.values() for s in a.values() for l in s]
            print(main_lines)
            m1, m2, m3, m4, m5, m6 = sum_group(main_lines)

            sheet.write(row_pos, 0, f"{main}", total_left)
            sheet.write(row_pos, 5, m1, total_right)
            sheet.write(row_pos, 6, m2, total_right)
            sheet.write(row_pos, 7, m3, total_right)
            sheet.write(row_pos, 8, m4, total_right)
            sheet.write(row_pos, 9, m5, total_right)
            sheet.write(row_pos, 10, m6, total_right)
            row_pos += 1

            for acc_type, subs in acc_types.items():

                acc_lines = [l for s in subs.values() for l in s]
                a1, a2, a3, a4, a5, a6 = sum_group(acc_lines)
                sheet.write(row_pos, 0, f"{main}", total_left)
                sheet.write(row_pos, 1, f"{acc_type}", total_left)
                sheet.write(row_pos, 5, a1, total_right)
                sheet.write(row_pos, 6, a2, total_right)
                sheet.write(row_pos, 7, a3, total_right)
                sheet.write(row_pos, 8, a4, total_right)
                sheet.write(row_pos, 9, a5, total_right)
                sheet.write(row_pos, 10, a6, total_right)
                row_pos += 1

                for sub, lines in subs.items():

                    s1, s2, s3, s4, s5, s6 = sum_group(lines)
                    sheet.write(row_pos, 0, f"{main}", total_left)
                    sheet.write(row_pos, 1, f"{acc_type}", total_left)
                    sheet.write(row_pos, 2, f"{sub}", total_left)
                    sheet.write(row_pos, 5, s1, total_right)
                    sheet.write(row_pos, 6, s2, total_right)
                    sheet.write(row_pos, 7, s3, total_right)
                    sheet.write(row_pos, 8, s4, total_right)
                    sheet.write(row_pos, 9, s5, total_right)
                    sheet.write(row_pos, 10, s6, total_right)
                    row_pos += 1

                    for l in lines:
                        sheet.write(row_pos, 0, main, fmt_left)
                        sheet.write(row_pos, 1, acc_type, fmt_left)
                        sheet.write(row_pos, 2, sub, fmt_left)
                        sheet.write(row_pos, 3, l["name"], fmt_left)
                        sheet.write(row_pos, 4, l["code"], fmt_center)

                        sheet.write(row_pos, 5, l["initial_debit"], fmt_right)
                        sheet.write(row_pos, 6, l["initial_credit"], fmt_right)
                        sheet.write(row_pos, 7, l["debit"], fmt_right)
                        sheet.write(row_pos, 8, l["credit"], fmt_right)
                        sheet.write(row_pos, 9, l["ending_debit"], fmt_right)
                        sheet.write(row_pos, 10, l["ending_credit"], fmt_right)
                        row_pos += 1

            row_pos += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file