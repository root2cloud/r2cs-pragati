# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by CandidRoot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
import io, base64
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

from odoo.tools.misc import xlsxwriter


class ReportWizard(models.TransientModel):
    _name = "stock.reports"
    _description = "stock report"

    start_date = fields.Datetime('Start date')
    end_date = fields.Datetime('End date')
    location_id = fields.Many2one('stock.location', 'Location')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('stock.reports'))
    filterby = fields.Selection([('no_filtred', ' No Filterd'), ('product', 'Product')],
                                'Filter by',
                                default='no_filtred')
    products = fields.Many2many('product.product', 'products')
    group_by_category = fields.Boolean('Group By Category')

    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()

    def _compute_initial_stock(self, product_ids, location_id, start_date):
        """Compute initial stock for products before the start_date."""
        initial_stock_dict = {}
        date_before_start = start_date - timedelta(days=1)

        # Query stock moves before start_date for initial stock
        domain = [
            ('date', '<=', date_before_start),
            ('product_id', 'in', product_ids),
            ('state', '=', 'done'),  # Only consider confirmed moves
        ]
        if location_id:
            domain_in = domain + [('location_dest_id', '=', location_id.id)]
            domain_out = domain + [('location_id', '=', location_id.id)]
        else:
            domain_in = domain + [('location_dest_id.usage', '=', 'internal')]
            domain_out = domain + [('location_id.usage', '=', 'internal')]

        # Incoming stock (moves to the location)
        incoming_moves = self.env['stock.move.line'].read_group(
            domain_in,
            ['product_id', 'qty_done:sum'],
            ['product_id']
        )
        for move in incoming_moves:
            product_id = move['product_id'][0]
            initial_stock_dict[product_id] = initial_stock_dict.get(product_id, 0) + move['qty_done']

        # Outgoing stock (moves from the location)
        outgoing_moves = self.env['stock.move.line'].read_group(
            domain_out,
            ['product_id', 'qty_done:sum'],
            ['product_id']
        )
        for move in outgoing_moves:
            product_id = move['product_id'][0]
            initial_stock_dict[product_id] = initial_stock_dict.get(product_id, 0) - move['qty_done']

        return initial_stock_dict

    def _calculate_totals(self, record_list):
        """Calculate total sums for initial stock, in, out, balance and value."""
        totals = {
            'initial_stock': sum(rec.get('initial_stock', 0) for rec in record_list),
            'in': sum(rec.get('in', 0) for rec in record_list),
            'out': sum(rec.get('out', 0) for rec in record_list),
            'balance': sum(rec.get('balance', 0) for rec in record_list),
            'value': sum(rec.get('value', 0) for rec in record_list),
        }
        return totals

    def _calculate_category_totals(self, category_dict):
        """Calculate totals for each category including value."""
        category_totals = {}
        for category_name, records in category_dict.items():
            category_totals[category_name] = self._calculate_totals(records)
        return category_totals

    def button_export_pdf(self):
        # Determine product filter
        if not self.products:
            if self.location_id:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                     ('location_dest_id', 'in', self.location_id.ids)], ['product_id'],
                    ['product_id'])
            else:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date)], ['product_id'],
                    ['product_id'])
        else:
            if self.location_id:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                     ('product_id', 'in', self.products.ids), ('location_dest_id', 'in', self.location_id.ids)],
                    fields=['product_id'],
                    groupby=['product_id'], lazy=False)
            else:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                     ('product_id', 'in', self.products.ids)],
                    fields=['product_id'],
                    groupby=['product_id'], lazy=False)

        filter_ids = []
        for rec in category_group:
            product_id = rec['product_id'][0]
            if product_id not in filter_ids:
                filter_ids.append(product_id)

        # Compute initial stock for filtered products
        initial_stock_dict = self._compute_initial_stock(filter_ids, self.location_id, self.start_date)

        all_search = self.env['stock.move.line'].search([('product_id', 'in', filter_ids)])
        search = []
        product_list = []
        for each_item in all_search:
            if each_item.product_id.id not in product_list:
                search.append(each_item)
            product_list.append(each_item.product_id.id)

        # Compute incoming and outgoing quantities within the date range
        object = self.env['stock.move.line'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('product_id', 'in', filter_ids),
            ('state', '=', 'done')
        ])
        incoming_dict = {}
        outgoing_dict = {}
        for rec in object:
            if self.location_id:
                if rec.location_dest_id == self.location_id:
                    incoming_dict[rec.product_id.id] = incoming_dict.get(rec.product_id.id, 0) + rec.qty_done
                if rec.location_id == self.location_id:
                    outgoing_dict[rec.product_id.id] = outgoing_dict.get(rec.product_id.id, 0) + rec.qty_done
            else:
                if rec.location_dest_id.usage == 'internal':
                    incoming_dict[rec.product_id.id] = incoming_dict.get(rec.product_id.id, 0) + rec.qty_done
                if rec.location_id.usage == 'internal':
                    outgoing_dict[rec.product_id.id] = outgoing_dict.get(rec.product_id.id, 0) + rec.qty_done

        record_list = []
        for res in search:
            initial_stock = initial_stock_dict.get(res.product_id.id, 0)
            in_com = incoming_dict.get(res.product_id.id, 0)
            out_go = outgoing_dict.get(res.product_id.id, 0)
            balance = initial_stock + in_com - out_go
            unit_price = res.product_id.lst_price  # unit price from product
            value = unit_price * balance  # calculated value

            vals = {
                'product': res.product_id.name,
                'default_code': res.product_id.default_code,
                'uom': res.product_uom_id.name,
                'reference': res.reference,
                'initial_stock': initial_stock,
                'hsn': res.product_id.product_tmpl_id.l10n_in_hsn_code or '',
                'in': in_com,
                'out': out_go,
                'balance': balance,
                'value': value,  # new field added
                'rec_set': res,
            }
            record_list.append(vals)

        # Calculate totals
        grand_totals = self._calculate_totals(record_list)

        category_dict = {}
        for rec_list in record_list:
            category_name = rec_list.get('rec_set').product_id.categ_id.name
            if category_name in category_dict:
                category_dict[category_name].append(rec_list)
            else:
                category_dict[category_name] = [rec_list]

        # Calculate category totals
        category_totals = self._calculate_category_totals(category_dict)

        locations = (self.read()[0]['location_id'] and self.read()[0]['location_id'][1]) or \
                    self.env['stock.location'].search([]).mapped('name')

        data = {
            'report_start_date': self.read()[0]['start_date'],
            'report_end_date': self.read()[0]['end_date'],
            'report_company_id': self.read()[0]['company_id'][1],
            'report_location': locations,
            # Add totals to data
            'total_initial_stock': grand_totals['initial_stock'],
            'total_in': grand_totals['in'],
            'total_out': grand_totals['out'],
            'total_balance': grand_totals['balance'],
            'total_value': grand_totals['value'],  # total value
        }

        if self.group_by_category:
            data.update({
                'search_record_grouped': category_dict,
                'category_totals': category_totals
            })
        else:
            data.update({
                'report_group_by_category': self.read()[0]['group_by_category'],
                'search_record': record_list,
            })

        return self.env.ref('stock_report_cr.action_report_stock_report').report_action(self, data=data)

    def button_export_xlsx(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Inventory Excel Report')

        # Determine product filter
        if not self.products:
            if self.location_id:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                     ('location_dest_id', 'in', self.location_id.ids)], ['product_id'],
                    ['product_id'])
            else:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date)], ['product_id'],
                    ['product_id'])
        else:
            if self.location_id:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                     ('product_id', 'in', self.products.ids), ('location_dest_id', 'in', self.location_id.ids)],
                    fields=['product_id'],
                    groupby=['product_id'], lazy=False)
            else:
                category_group = self.env['stock.move.line'].read_group(
                    [('date', '>=', self.start_date), ('date', '<=', self.end_date),
                     ('product_id', 'in', self.products.ids)],
                    fields=['product_id'],
                    groupby=['product_id'], lazy=False)

        filter_ids = []
        for rec in category_group:
            product_id = rec['product_id'][0]
            if product_id not in filter_ids:
                filter_ids.append(product_id)

        # Compute initial stock for filtered products
        initial_stock_dict = self._compute_initial_stock(filter_ids, self.location_id, self.start_date)

        all_search = self.env['stock.move.line'].search([('product_id', 'in', filter_ids)])
        search = []
        product_list = []
        for each_item in all_search:
            if each_item.product_id.id not in product_list:
                search.append(each_item)
            product_list.append(each_item.product_id.id)

        # Compute incoming and outgoing quantities within the date range
        object = self.env['stock.move.line'].search([
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('product_id', 'in', filter_ids),
            ('state', '=', 'done')
        ])
        incoming_dict = {}
        outgoing_dict = {}
        for rec in object:
            if self.location_id:
                if rec.location_dest_id == self.location_id:
                    incoming_dict[rec.product_id.id] = incoming_dict.get(rec.product_id.id, 0) + rec.qty_done
                if rec.location_id == self.location_id:
                    outgoing_dict[rec.product_id.id] = outgoing_dict.get(rec.product_id.id, 0) + rec.qty_done
            else:
                if rec.location_dest_id.usage == 'internal':
                    incoming_dict[rec.product_id.id] = incoming_dict.get(rec.product_id.id, 0) + rec.qty_done
                if rec.location_id.usage == 'internal':
                    outgoing_dict[rec.product_id.id] = outgoing_dict.get(rec.product_id.id, 0) + rec.qty_done

        record_list = []
        for res in search:
            initial_stock = initial_stock_dict.get(res.product_id.id, 0)
            in_com = incoming_dict.get(res.product_id.id, 0)
            out_go = outgoing_dict.get(res.product_id.id, 0)
            balance = initial_stock + in_com - out_go
            unit_price = res.product_id.lst_price  # unit price from product
            value = unit_price * balance  # calculated value

            vals = {
                'product': res.product_id.name,
                'default_code': res.product_id.default_code,
                'uom': res.product_uom_id.name,
                'reference': res.reference,
                'initial_stock': initial_stock,
                'hsn': res.product_id.product_tmpl_id.l10n_in_hsn_code or '',
                'in': in_com,
                'out': out_go,
                'balance': balance,
                'value': value,  # new field added
                'rec_set': res,
            }
            record_list.append(vals)

        # Calculate totals for Excel
        grand_totals = self._calculate_totals(record_list)

        category_dict = {}
        for rec_list in record_list:
            category_name = rec_list.get('rec_set').product_id.categ_id.name
            if category_name in category_dict:
                category_dict[category_name].append(rec_list)
            else:
                category_dict[category_name] = [rec_list]

        # Calculate category totals for Excel
        category_totals = self._calculate_category_totals(category_dict)

        # Write to Excel
        header_style = workbook.add_format({'bold': True, 'align': 'center'})
        date_style = workbook.add_format({'align': 'center', 'num_format': 'dd-mm-yyyy'})
        total_style = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#90EE90'})
        subtotal_style = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#ADD8E6'})

        locations = self.env['stock.location'].search([])
        locations_name = ', '.join(locations.mapped('name'))

        sheet.write(0, 0, 'Warehouse', header_style)
        sheet.write(2, 0, 'Location', header_style)
        sheet.write(4, 0, 'Start Date', header_style)
        sheet.write(6, 0, 'End Date', header_style)
        sheet.write(0, 1, self.company_id.name, date_style)
        sheet.write(2, 1, self.location_id.name or locations_name, date_style)
        sheet.write(4, 1, self.start_date, date_style)
        sheet.write(6, 1, self.end_date, date_style)

        sheet.set_column('A2:E5', 27)
        head_style = workbook.add_format({'align': 'center', 'bold': True, 'bg_color': '#dedede'})
        row_head = 8
        sheet.write(row_head, 0, 'Reference', head_style)
        sheet.write(row_head, 1, 'Designation', head_style)
        sheet.write(row_head, 2, 'UoM', head_style)
        sheet.write(row_head, 3, 'HSN', head_style)
        sheet.write(row_head, 4, 'Initial stock', head_style)
        sheet.write(row_head, 5, 'IN', head_style)
        sheet.write(row_head, 6, 'OUT', head_style)
        sheet.write(row_head, 7, 'Balance', head_style)
        sheet.write(row_head, 8, 'Value', head_style)
        sheet.freeze_panes(10, 0)

        categ_style = workbook.add_format({'bg_color': '#dedede', 'align': 'center'})
        data_font_style = workbook.add_format({'align': 'center'})
        row = 10

        if self.group_by_category:
            for main in category_dict:
                sheet.write(row, 0, main, categ_style)
                sheet.write(row, 1, '', categ_style)
                sheet.write(row, 2, '', categ_style)
                sheet.write(row, 3, '', categ_style)
                sheet.write(row, 4, '', categ_style)
                sheet.write(row, 5, '', categ_style)
                sheet.write(row, 6, '', categ_style)
                sheet.write(row, 7, '', categ_style)
                sheet.write(row, 8, '', categ_style)
                for line in category_dict[main]:
                    row += 1
                    sheet.write(row, 0, line.get('default_code'), data_font_style)
                    sheet.write(row, 1, line.get('product'), data_font_style)
                    sheet.write(row, 2, line.get('uom'), data_font_style)
                    sheet.write(row, 3, line.get('hsn'), data_font_style)
                    sheet.write(row, 4, line.get('initial_stock'), data_font_style)
                    sheet.write(row, 5, line.get('in'), data_font_style)
                    sheet.write(row, 6, line.get('out'), data_font_style)
                    sheet.write(row, 7, line.get('balance'), data_font_style)
                    sheet.write(row, 8, line.get('value'), data_font_style)  # new column value

                # Add category subtotal
                row += 1
                sheet.write(row, 0, 'Category Subtotal:', subtotal_style)
                sheet.write(row, 1, '', subtotal_style)
                sheet.write(row, 2, '', subtotal_style)
                sheet.write(row, 3, '', subtotal_style)
                sheet.write(row, 4, category_totals[main]['initial_stock'], subtotal_style)
                sheet.write(row, 5, category_totals[main]['in'], subtotal_style)
                sheet.write(row, 6, category_totals[main]['out'], subtotal_style)
                sheet.write(row, 7, category_totals[main]['balance'], subtotal_style)
                sheet.write(row, 8, category_totals[main]['value'], subtotal_style)  # subtotal value
                row += 2
        else:
            for line in record_list:
                row += 1
                sheet.write(row, 0, line.get('default_code'), data_font_style)
                sheet.write(row, 1, line.get('product'), data_font_style)
                sheet.write(row, 2, line.get('uom'), data_font_style)
                sheet.write(row, 3, line.get('hsn'), data_font_style)
                sheet.write(row, 4, line.get('initial_stock'), data_font_style)
                sheet.write(row, 5, line.get('in'), data_font_style)
                sheet.write(row, 6, line.get('out'), data_font_style)
                sheet.write(row, 7, line.get('balance'), data_font_style)
                sheet.write(row, 8, line.get('value'), data_font_style)  # new column value

        # Add grand total row
        row += 2
        sheet.write(row, 0, 'GRAND TOTAL:', total_style)
        sheet.write(row, 1, '', total_style)
        sheet.write(row, 2, '', total_style)
        sheet.write(row, 3, '', total_style)
        sheet.write(row, 4, grand_totals['initial_stock'], total_style)
        sheet.write(row, 5, grand_totals['in'], total_style)
        sheet.write(row, 6, grand_totals['out'], total_style)
        sheet.write(row, 7, grand_totals['balance'], total_style)
        sheet.write(row, 8, grand_totals['value'], total_style)  # grand total value

        workbook.close()
        xlsx_data = output.getvalue()
        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "Stock Excel Report.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'name': 'Inventory Excel Report',
            'url': '/web/content/stock.reports/%s/xls_file/%s?download=true' % (
                self.id, 'Stock Excel Report.xlsx'),
        }
