from odoo import models, fields, api
import io
import xlsxwriter
from odoo.tools import date_utils


class CouponExcelReport(models.AbstractModel):
    _name = 'report.coupon_issue_pragati.coupon_excel_report'

    def generate_xlsx_report(self, workbook, data, coupons):
        # Create sheet
        sheet = workbook.add_worksheet('Coupon Report')

        # Define formats
        bold = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1})
        currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        border_format = workbook.add_format({'border': 1})

        # Set column widths for landscape layout
        sheet.set_column('A:A', 15)   # Reference
        sheet.set_column('B:B', 20)   # Coupon Code
        sheet.set_column('C:C', 25)   # Customer
        sheet.set_column('D:D', 20)   # Designation
        sheet.set_column('E:E', 12)   # No. of Persons
        sheet.set_column('F:F', 15)   # Coupon Value
        sheet.set_column('G:G', 15)   # Issue Date
        sheet.set_column('H:H', 15)   # Expiry Date
        sheet.set_column('I:I', 20)   # Salesperson
        sheet.set_column('J:J', 15)   # Status
        sheet.set_column('K:K', 20)   # Redeemed Date
        sheet.set_column('L:L', 20)   # Redeemed By

        # Write headers with Designation column
        headers = [
            'Reference', 'Coupon Code', 'Customer', 'Designation',
            'No. of Persons', 'Coupon Value', 'Issue Date', 'Expiry Date',
            'Salesperson', 'Status', 'Redeemed Date', 'Redeemed By'
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_format)

        # Write data
        row = 1
        total_value = 0
        total_issued = len(coupons)
        total_redeemed = 0

        for coupon in coupons:
            # Check if redeemed
            redeem = self.env['coupon.redeem'].search([
                ('coupon_issue_id', '=', coupon.id),
                ('state', '=', 'redeemed')
            ], limit=1)

            redeemed_date = ''
            redeemed_by = ''
            no_of_persons = ''

            if redeem:
                redeemed_date = redeem.redeem_date
                redeemed_by = redeem.redeem_by.name
                no_of_persons = redeem.no_of_persons
                total_redeemed += 1

            # Write row data with Designation
            sheet.write(row, 0, coupon.name, border_format)
            sheet.write(row, 1, coupon.coupon_code, border_format)
            sheet.write(row, 2, coupon.customer_id.name or '', border_format)
            sheet.write(row, 3, coupon.designation or '', border_format)  # Designation column
            sheet.write(row, 4, no_of_persons, border_format)
            sheet.write(row, 5, coupon.coupon_value, currency_format)
            sheet.write(row, 6, coupon.issue_date or '', date_format)
            sheet.write(row, 7, coupon.expiry_date or '', date_format)
            sheet.write(row, 8, coupon.salespersons_name or '', border_format)
            sheet.write(row, 9, coupon.state, border_format)
            sheet.write(row, 10, redeemed_date, date_format)
            sheet.write(row, 11, redeemed_by, border_format)

            total_value += coupon.coupon_value
            row += 1

        # Write summary
        summary_row = row + 2
        sheet.write(summary_row, 0, 'SUMMARY', bold)
        sheet.write(summary_row + 1, 0, 'Total Issued:', bold)
        sheet.write(summary_row + 1, 1, total_issued, border_format)
        sheet.write(summary_row + 2, 0, 'Total Redeemed:', bold)
        sheet.write(summary_row + 2, 1, total_redeemed, border_format)
        sheet.write(summary_row + 3, 0, 'Total Value:', bold)
        sheet.write(summary_row + 3, 1, total_value, currency_format)
        sheet.write(summary_row + 4, 0, 'Report Date:', bold)
        sheet.write(summary_row + 4, 1, fields.Date.today(), date_format)

# from odoo import models, fields, api
# import io
# import xlsxwriter
# from odoo.tools import date_utils
#
#
# class CouponExcelReport(models.AbstractModel):
#     _name = 'report.coupon_issue_pragati.coupon_excel_report'
#     # _inherit = 'report.report_xlsx.abstract'
#
#     def generate_xlsx_report(self, workbook, data, coupons):
#         # Create sheet
#         sheet = workbook.add_worksheet('Coupon Report')
#
#         # Define formats
#         bold = workbook.add_format({'bold': True})
#         header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
#         date_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'border': 1})
#         currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
#         border_format = workbook.add_format({'border': 1})
#
#         # Set column widths
#         sheet.set_column('A:A', 15)
#         sheet.set_column('B:B', 20)
#         sheet.set_column('C:C', 25)
#         sheet.set_column('D:D', 15)
#         sheet.set_column('E:E', 15)
#         sheet.set_column('F:F', 15)
#         sheet.set_column('G:G', 20)
#         sheet.set_column('H:H', 20)
#         sheet.set_column('I:I', 20)
#         sheet.set_column('J:J', 20)
#         sheet.set_column('K:K', 20)
#
#         # Write headers
#         headers = [
#             'Reference', 'Coupon Code', 'Customer', 'Coupon Value',
#             'Issue Date', 'Expiry Date', 'Salesperson', 'Status',
#             'Redeemed Date', 'Redeemed By', 'No. of Persons'
#         ]
#
#         for col, header in enumerate(headers):
#             sheet.write(0, col, header, header_format)
#
#         # Write data
#         row = 1
#         total_value = 0
#         total_issued = len(coupons)
#         total_redeemed = 0
#
#         for coupon in coupons:
#             # Check if redeemed
#             redeem = self.env['coupon.redeem'].search([
#                 ('coupon_issue_id', '=', coupon.id),
#                 ('state', '=', 'redeemed')
#             ], limit=1)
#
#             redeemed_date = ''
#             redeemed_by = ''
#             no_of_persons = ''
#
#             if redeem:
#                 redeemed_date = redeem.redeem_date
#                 redeemed_by = redeem.redeem_by.name
#                 no_of_persons = redeem.no_of_persons
#                 total_redeemed += 1
#
#             # Write row data
#             sheet.write(row, 0, coupon.name, border_format)
#             sheet.write(row, 1, coupon.coupon_code, border_format)
#             sheet.write(row, 2, coupon.customer_id.name or '', border_format)
#             sheet.write(row, 3, coupon.coupon_value, currency_format)
#             sheet.write(row, 4, coupon.issue_date or '', date_format)
#             sheet.write(row, 5, coupon.expiry_date or '', date_format)
#             sheet.write(row, 6, coupon.salesperson_id.name or '', border_format)
#             sheet.write(row, 7, coupon.state, border_format)
#             sheet.write(row, 8, redeemed_date, date_format)
#             sheet.write(row, 9, redeemed_by, border_format)
#             sheet.write(row, 10, no_of_persons, border_format)
#
#             total_value += coupon.coupon_value
#             row += 1
#
#         # Write summary
#         summary_row = row + 2
#         sheet.write(summary_row, 0, 'SUMMARY', bold)
#         sheet.write(summary_row + 1, 0, 'Total Issued:', bold)
#         sheet.write(summary_row + 1, 1, total_issued, border_format)
#         sheet.write(summary_row + 2, 0, 'Total Redeemed:', bold)
#         sheet.write(summary_row + 2, 1, total_redeemed, border_format)
#         sheet.write(summary_row + 3, 0, 'Total Value:', bold)
#         sheet.write(summary_row + 3, 1, total_value, currency_format)
#         sheet.write(summary_row + 4, 0, 'Report Date:', bold)
#         sheet.write(summary_row + 4, 1, fields.Date.today(), date_format)