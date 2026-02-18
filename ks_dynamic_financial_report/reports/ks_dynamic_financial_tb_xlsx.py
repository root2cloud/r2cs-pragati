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
        ks_company_id = self.env['res.company'].sudo().browse(
            ks_df_informations.get('company_id')
        )

        sheet = workbook.add_worksheet('Trial Balance')

        # ✅ COLUMN ORDER (Particulars First, Groups Last)
        sheet.set_column(0, 0, 40)  # Particulars
        sheet.set_column(1, 1, 12)  # Code
        sheet.set_column(2, 7, 15)  # Amount Columns
        sheet.set_column(8, 10, 25)  # Group Columns

        # ================= FORMATS =================
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
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })

        format_subheader = workbook.add_format({
            'bold': True, 'align': 'center',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })

        fmt_left = workbook.add_format({'border': 1, 'align': 'left'})
        fmt_center = workbook.add_format({'border': 1, 'align': 'center'})
        fmt_right = workbook.add_format({'border': 1, 'align': 'right'})
        fmt_right.set_num_format('#,##0.00')

        # ================= DATE RANGE =================
        start_date = ks_df_informations['date']['ks_start_date']
        end_date = ks_df_informations['date']['ks_end_date']

        start_fmt = datetime.datetime.strptime(
            start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        end_fmt = datetime.datetime.strptime(
            end_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        date_range_text = f"[Custom Range ({start_fmt} to {end_fmt})]"

        # ================= TITLE =================
        sheet.merge_range(row_pos, 0, row_pos, 10,
                          ks_company_id.name.upper(), format_company)
        row_pos += 1

        sheet.merge_range(row_pos, 0, row_pos, 10,
                          "TRIAL BALANCE", format_title)
        row_pos += 1

        sheet.merge_range(row_pos, 0, row_pos, 10,
                          date_range_text, format_date_range)
        row_pos += 2

        # ================= HEADER =================
        sheet.write(row_pos, 0, "Particulars", format_header)
        sheet.write(row_pos, 1, "Code", format_header)

        sheet.merge_range(row_pos, 2, row_pos, 3,
                          "Opening Balance", format_header)
        sheet.merge_range(row_pos, 4, row_pos, 5,
                          "Transaction", format_header)
        sheet.merge_range(row_pos, 6, row_pos, 7,
                          "Closing Balance", format_header)

        sheet.write(row_pos, 8, "Main Group", format_header)
        sheet.write(row_pos, 9, "Account Type", format_header)
        sheet.write(row_pos, 10, "Sub Type", format_header)

        row_pos += 1

        # ================= SUB HEADER =================
        sheet.write(row_pos, 0, "", format_subheader)
        sheet.write(row_pos, 1, "", format_subheader)

        sheet.write(row_pos, 2, "Dr (Op)", format_subheader)
        sheet.write(row_pos, 3, "Cr (Op)", format_subheader)
        sheet.write(row_pos, 4, "Debits", format_subheader)
        sheet.write(row_pos, 5, "Credits", format_subheader)
        sheet.write(row_pos, 6, "Dr (YTD)", format_subheader)
        sheet.write(row_pos, 7, "Cr (YTD)", format_subheader)

        sheet.write(row_pos, 8, "", format_subheader)
        sheet.write(row_pos, 9, "", format_subheader)
        sheet.write(row_pos, 10, "", format_subheader)

        row_pos += 1

        # ================= ONLY ACCOUNT LINES =================
        for account_code, line in move_lines.items():

            sheet.write(row_pos, 0, line.get("name"), fmt_left)
            sheet.write(row_pos, 1, line.get("code"), fmt_center)

            sheet.write(row_pos, 2, line.get("initial_debit", 0.0), fmt_right)
            sheet.write(row_pos, 3, line.get("initial_credit", 0.0), fmt_right)
            sheet.write(row_pos, 4, line.get("debit", 0.0), fmt_right)
            sheet.write(row_pos, 5, line.get("credit", 0.0), fmt_right)
            sheet.write(row_pos, 6, line.get("ending_debit", 0.0), fmt_right)
            sheet.write(row_pos, 7, line.get("ending_credit", 0.0), fmt_right)

            sheet.write(row_pos, 8, line.get("main_type") or "", fmt_left)
            sheet.write(row_pos, 9, line.get("account_type") or "", fmt_left)
            sheet.write(row_pos, 10, line.get("sub_type") or "", fmt_left)

            row_pos += 1

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
