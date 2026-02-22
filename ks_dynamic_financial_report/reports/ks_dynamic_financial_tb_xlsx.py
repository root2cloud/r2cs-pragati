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

        # Hide default Excel gridlines and freeze panes
        sheet.hide_gridlines(2)
        sheet.freeze_panes(6, 2)  # Freezes headers and the first 2 columns

        # ================= ADJUSTED COLUMN WIDTHS =================
        sheet.set_column(0, 0, 15)  # Code
        sheet.set_column(1, 1, 45)  # Account Name
        sheet.set_column(2, 7, 18)  # Amount Columns
        sheet.set_column(8, 9, 20)  # Main Group & Account Type
        sheet.set_column(10, 11, 20)  # Sub Type (Merged across 10 & 11 for massive width)

        # ================= PROFESSIONAL FORMATS =================
        color_primary = '#2d5b8c'
        color_secondary = '#e2e6eb'
        color_text_dark = '#1a3654'
        color_alt_row = '#f8f9fa'

        format_company = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'font_size': 16, 'font_color': color_primary, 'border': 0
        })

        format_title = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'font_size': 14, 'bg_color': color_primary,
            'font_color': 'white', 'border': 1, 'border_color': color_primary
        })

        format_date_range = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'italic': False, 'font_size': 11, 'font_color': '#333333'
        })

        # Main Header Format
        format_header = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'bg_color': color_primary, 'font_color': 'white',
            'border': 1, 'border_color': '#b5c4d3'
        })

        # Subheader Format
        format_subheader = workbook.add_format({
            'bold': True, 'align': 'center', 'valign': 'vcenter',
            'bg_color': color_secondary, 'font_color': color_text_dark,
            'border': 1, 'border_color': '#b5c4d3'
        })

        # Base Data Row Formatting (Added text_wrap for long Sub Types just in case)
        base_fmt = {'valign': 'vcenter', 'border': 1, 'border_color': '#ced4da', 'font_size': 11, 'text_wrap': True}
        acct_num_fmt = '#,##0.00'

        # Standard Row Formats
        fmt_left = workbook.add_format({**base_fmt, 'align': 'left'})
        fmt_center = workbook.add_format({**base_fmt, 'align': 'center', 'font_color': color_primary, 'bold': True})
        fmt_right = workbook.add_format({**base_fmt, 'align': 'right', 'num_format': acct_num_fmt})

        # Alternating (Zebra) Row Formats
        fmt_left_alt = workbook.add_format({**base_fmt, 'align': 'left', 'bg_color': color_alt_row})
        fmt_center_alt = workbook.add_format(
            {**base_fmt, 'align': 'center', 'font_color': color_primary, 'bold': True, 'bg_color': color_alt_row})
        fmt_right_alt = workbook.add_format(
            {**base_fmt, 'align': 'right', 'num_format': acct_num_fmt, 'bg_color': color_alt_row})

        # ================= DATE RANGE LOGIC =================
        start_date = ks_df_informations['date']['ks_start_date']
        end_date = ks_df_informations['date']['ks_end_date']

        start_fmt = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
        end_fmt = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')

        date_range_text = f"Period: {start_fmt} to {end_fmt}"
        column_date_range = f"{start_fmt} to {end_fmt}"

        # ================= WRITE TOP TITLES (Merged up to 11 now) =================
        sheet.set_row(row_pos, 25)
        sheet.merge_range(row_pos, 0, row_pos, 11, ks_company_id.name.upper(), format_company)
        row_pos += 1

        sheet.set_row(row_pos, 22)
        sheet.merge_range(row_pos, 0, row_pos, 11, "TRIAL BALANCE", format_title)
        row_pos += 1

        sheet.set_row(row_pos, 18)
        sheet.merge_range(row_pos, 0, row_pos, 11, date_range_text, format_date_range)
        row_pos += 2

        # ================= MAIN & SUB HEADERS =================
        sheet.set_row(row_pos, 22)

        # Code & Account Name
        sheet.merge_range(row_pos, 0, row_pos + 1, 0, "Code", format_header)
        sheet.merge_range(row_pos, 1, row_pos + 1, 1, "Account Name", format_header)

        # Amounts
        sheet.merge_range(row_pos, 2, row_pos, 3, "Opening Balance", format_header)
        sheet.merge_range(row_pos, 4, row_pos, 5, column_date_range, format_header)
        sheet.merge_range(row_pos, 6, row_pos, 7, "Ending Balance", format_header)

        # Groups (Sub Type merged across 10 and 11)
        sheet.merge_range(row_pos, 8, row_pos + 1, 8, "Main Group", format_header)
        sheet.merge_range(row_pos, 9, row_pos + 1, 9, "Account Type", format_header)
        sheet.merge_range(row_pos, 10, row_pos + 1, 11, "Sub Type", format_header)

        row_pos += 1

        # Write the sub-headers into the split columns
        sheet.set_row(row_pos, 20)
        sheet.write(row_pos, 2, "Debit", format_subheader)
        sheet.write(row_pos, 3, "Credit", format_subheader)
        sheet.write(row_pos, 4, "Debit", format_subheader)
        sheet.write(row_pos, 5, "Credit", format_subheader)
        sheet.write(row_pos, 6, "Debit", format_subheader)
        sheet.write(row_pos, 7, "Credit", format_subheader)

        row_pos += 1

        # ================= WRITE ACCOUNT LINES =================
        is_alt_row = False
        for account_code, line in move_lines.items():
            sheet.set_row(row_pos, 18)

            c_left = fmt_left_alt if is_alt_row else fmt_left
            c_center = fmt_center_alt if is_alt_row else fmt_center
            c_right = fmt_right_alt if is_alt_row else fmt_right

            # Code & Name
            sheet.write(row_pos, 0, line.get("code"), c_center)
            sheet.write(row_pos, 1, line.get("name"), c_left)

            # Amounts
            sheet.write(row_pos, 2, line.get("initial_debit", 0.0), c_right)
            sheet.write(row_pos, 3, line.get("initial_credit", 0.0), c_right)
            sheet.write(row_pos, 4, line.get("debit", 0.0), c_right)
            sheet.write(row_pos, 5, line.get("credit", 0.0), c_right)
            sheet.write(row_pos, 6, line.get("ending_debit", 0.0), c_right)
            sheet.write(row_pos, 7, line.get("ending_credit", 0.0), c_right)

            # Groups (Notice the merge_range for Sub Type)
            sheet.write(row_pos, 8, line.get("main_type") or "", c_left)
            sheet.write(row_pos, 9, line.get("account_type") or "", c_left)
            sheet.merge_range(row_pos, 10, row_pos, 11, line.get("sub_type") or "", c_left)

            row_pos += 1
            is_alt_row = not is_alt_row

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file
