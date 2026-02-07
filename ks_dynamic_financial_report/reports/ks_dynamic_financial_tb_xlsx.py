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

        # Set column widths - NEW ORDER: Particulars first, then Code, then balances, then group info
        sheet.set_column(0, 0, 40)  # Particulars
        sheet.set_column(1, 1, 12)  # Code
        sheet.set_column(2, 2, 15)  # Opening Dr
        sheet.set_column(3, 3, 15)  # Opening Cr
        sheet.set_column(4, 4, 15)  # Debits
        sheet.set_column(5, 5, 15)  # Credits
        sheet.set_column(6, 6, 15)  # Closing Dr
        sheet.set_column(7, 7, 15)  # Closing Cr
        sheet.set_column(8, 8, 25)  # Main Group
        sheet.set_column(9, 9, 25)  # Account Type
        sheet.set_column(10, 10, 25)  # Sub Type

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

        # Main headers - NEW ORDER: Particulars first
        sheet.write(row_pos, 0, "Particulars", format_header)
        sheet.write(row_pos, 1, "Code", format_header)
        sheet.merge_range(row_pos, 2, row_pos, 3, "Opening Balance", format_header)
        sheet.merge_range(row_pos, 4, row_pos, 5, "Transaction", format_header)
        sheet.merge_range(row_pos, 6, row_pos, 7, "Closing Balance", format_header)
        sheet.write(row_pos, 8, "Main Group", format_header)
        sheet.write(row_pos, 9, "Account Type", format_header)
        sheet.write(row_pos, 10, "Sub Type", format_header)
        row_pos += 1

        # Sub headers - NEW ORDER
        sheet.write(row_pos, 0, "", format_subheader)  # Particulars
        sheet.write(row_pos, 1, "", format_subheader)  # Code
        sheet.write(row_pos, 2, "Dr (Op)", format_subheader)
        sheet.write(row_pos, 3, "Cr (Op)", format_subheader)
        sheet.write(row_pos, 4, "Debits", format_subheader)
        sheet.write(row_pos, 5, "Credits", format_subheader)
        sheet.write(row_pos, 6, "Dr (YTD)", format_subheader)
        sheet.write(row_pos, 7, "Cr (YTD)", format_subheader)
        sheet.write(row_pos, 8, "", format_subheader)  # Main Group
        sheet.write(row_pos, 9, "", format_subheader)  # Account Type
        sheet.write(row_pos, 10, "", format_subheader)  # Sub Type
        row_pos += 1

        hierarchy = {}
        for account_code, line in move_lines.items():
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
            m1, m2, m3, m4, m5, m6 = sum_group(main_lines)

            # Main group total row - NEW COLUMN ORDER
            sheet.write(row_pos, 0, "", total_left)  # Particulars
            sheet.write(row_pos, 1, "", total_left)  # Code
            sheet.write(row_pos, 2, m1, total_right)  # Dr (Op)
            sheet.write(row_pos, 3, m2, total_right)  # Cr (Op)
            sheet.write(row_pos, 4, m3, total_right)  # Debits
            sheet.write(row_pos, 5, m4, total_right)  # Credits
            sheet.write(row_pos, 6, m5, total_right)  # Dr (YTD)
            sheet.write(row_pos, 7, m6, total_right)  # Cr (YTD)
            sheet.write(row_pos, 8, f"{main}", total_left)  # Main Group
            sheet.write(row_pos, 9, "", total_left)  # Account Type
            sheet.write(row_pos, 10, "", total_left)  # Sub Type
            row_pos += 1

            for acc_type, subs in acc_types.items():
                acc_lines = [l for s in subs.values() for l in s]
                a1, a2, a3, a4, a5, a6 = sum_group(acc_lines)

                # Account type total row - NEW COLUMN ORDER
                sheet.write(row_pos, 0, "", total_left)  # Particulars
                sheet.write(row_pos, 1, "", total_left)  # Code
                sheet.write(row_pos, 2, a1, total_right)  # Dr (Op)
                sheet.write(row_pos, 3, a2, total_right)  # Cr (Op)
                sheet.write(row_pos, 4, a3, total_right)  # Debits
                sheet.write(row_pos, 5, a4, total_right)  # Credits
                sheet.write(row_pos, 6, a5, total_right)  # Dr (YTD)
                sheet.write(row_pos, 7, a6, total_right)  # Cr (YTD)
                sheet.write(row_pos, 8, f"{main}", total_left)  # Main Group
                sheet.write(row_pos, 9, f"{acc_type}", total_left)  # Account Type
                sheet.write(row_pos, 10, "", total_left)  # Sub Type
                row_pos += 1

                for sub, lines in subs.items():
                    s1, s2, s3, s4, s5, s6 = sum_group(lines)

                    # Sub type total row - NEW COLUMN ORDER
                    sheet.write(row_pos, 0, "", total_left)  # Particulars
                    sheet.write(row_pos, 1, "", total_left)  # Code
                    sheet.write(row_pos, 2, s1, total_right)  # Dr (Op)
                    sheet.write(row_pos, 3, s2, total_right)  # Cr (Op)
                    sheet.write(row_pos, 4, s3, total_right)  # Debits
                    sheet.write(row_pos, 5, s4, total_right)  # Credits
                    sheet.write(row_pos, 6, s5, total_right)  # Dr (YTD)
                    sheet.write(row_pos, 7, s6, total_right)  # Cr (YTD)
                    sheet.write(row_pos, 8, f"{main}", total_left)  # Main Group
                    sheet.write(row_pos, 9, f"{acc_type}", total_left)  # Account Type
                    sheet.write(row_pos, 10, f"{sub}", total_left)  # Sub Type
                    row_pos += 1

                    for l in lines:
                        # Individual account rows - NEW COLUMN ORDER
                        sheet.write(row_pos, 0, l["name"], fmt_left)  # Particulars
                        sheet.write(row_pos, 1, l["code"], fmt_center)  # Code
                        sheet.write(row_pos, 2, l["initial_debit"], fmt_right)  # Dr (Op)
                        sheet.write(row_pos, 3, l["initial_credit"], fmt_right)  # Cr (Op)
                        sheet.write(row_pos, 4, l["debit"], fmt_right)  # Debits
                        sheet.write(row_pos, 5, l["credit"], fmt_right)  # Credits
                        sheet.write(row_pos, 6, l["ending_debit"], fmt_right)  # Dr (YTD)
                        sheet.write(row_pos, 7, l["ending_credit"], fmt_right)  # Cr (YTD)
                        sheet.write(row_pos, 8, main, fmt_left)  # Main Group
                        sheet.write(row_pos, 9, acc_type, fmt_left)  # Account Type
                        sheet.write(row_pos, 10, sub, fmt_left)  # Sub Type
                        row_pos += 1

            row_pos += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file