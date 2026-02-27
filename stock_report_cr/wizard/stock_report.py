# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by CandidRoot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import io, base64
import logging
from datetime import datetime, timedelta, time
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

from odoo.tools.misc import xlsxwriter


class ReportWizard(models.TransientModel):
    _name = "stock.reports"
    _description = "stock report"

    date_range = fields.Selection([
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('custom', 'Custom')
    ], string='Date Filter', default='today', required=True)

    start_date = fields.Date('Start date', required=True, default=fields.Date.context_today)
    end_date = fields.Date('End date', required=True, default=fields.Date.context_today)

    location_ids = fields.Many2many('stock.location', string='Locations')

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('stock.reports'))
    filterby = fields.Selection([('no_filtred', ' No Filterd'), ('product', 'Product')],
                                'Filter by',
                                default='no_filtred')
    products = fields.Many2many('product.product', 'products')
    group_by_category = fields.Boolean('Group By Category')

    xls_file = fields.Binary(string="XLS file")
    xls_filename = fields.Char()

    @api.onchange('date_range')
    def _onchange_date_range(self):
        today = fields.Date.context_today(self)
        if self.date_range == 'today':
            self.start_date = today
            self.end_date = today
        elif self.date_range == 'yesterday':
            self.start_date = today - timedelta(days=1)
            self.end_date = today - timedelta(days=1)
        elif self.date_range == 'this_week':
            self.start_date = today - timedelta(days=today.weekday())
            self.end_date = self.start_date + timedelta(days=6)
        elif self.date_range == 'last_week':
            self.start_date = today - timedelta(days=today.weekday() + 7)
            self.end_date = self.start_date + timedelta(days=6)
        elif self.date_range == 'this_month':
            self.start_date = today.replace(day=1)
            self.end_date = (today + relativedelta(months=1, day=1)) - timedelta(days=1)
        elif self.date_range == 'last_month':
            self.start_date = today - relativedelta(months=1, day=1)
            self.end_date = today.replace(day=1) - timedelta(days=1)

    def _compute_initial_stock(self, product_ids, location_ids, start_date):
        initial_stock_dict = {}
        domain = [('date', '<', start_date), ('state', '=', 'done')]
        if product_ids:
            domain.append(('product_id', 'in', product_ids))

        if location_ids:
            domain_in = domain + [('location_dest_id', 'in', location_ids.ids)]
            domain_out = domain + [('location_id', 'in', location_ids.ids)]
        else:
            domain_in = domain + [('location_dest_id.usage', '=', 'internal')]
            domain_out = domain + [('location_id.usage', '=', 'internal')]

        incoming_moves = self.env['stock.move.line'].read_group(domain_in,
                                                                ['product_id', 'location_dest_id', 'qty_done:sum'],
                                                                ['product_id', 'location_dest_id'], lazy=False)
        for move in incoming_moves:
            key = (move['location_dest_id'][0], move['product_id'][0])
            initial_stock_dict[key] = initial_stock_dict.get(key, 0) + move['qty_done']

        outgoing_moves = self.env['stock.move.line'].read_group(domain_out,
                                                                ['product_id', 'location_id', 'qty_done:sum'],
                                                                ['product_id', 'location_id'], lazy=False)
        for move in outgoing_moves:
            key = (move['location_id'][0], move['product_id'][0])
            initial_stock_dict[key] = initial_stock_dict.get(key, 0) - move['qty_done']

        return initial_stock_dict

    def _get_report_data(self, start_dt, end_dt):
        domain_prod = [('product_id', 'in', self.products.ids)] if self.products else []
        initial_stock_dict = self._compute_initial_stock(self.products.ids if self.products else [], self.location_ids,
                                                         start_dt)

        domain_in = [('date', '>=', start_dt), ('date', '<=', end_dt), ('state', '=', 'done')] + domain_prod
        domain_out = list(domain_in)

        if self.location_ids:
            domain_in.append(('location_dest_id', 'in', self.location_ids.ids))
            domain_out.append(('location_id', 'in', self.location_ids.ids))
        else:
            domain_in.append(('location_dest_id.usage', '=', 'internal'))
            domain_out.append(('location_id.usage', '=', 'internal'))

        incoming_moves = self.env['stock.move.line'].read_group(domain_in,
                                                                ['product_id', 'location_dest_id', 'qty_done:sum'],
                                                                ['product_id', 'location_dest_id'], lazy=False)
        incoming_dict = {}
        for move in incoming_moves:
            key = (move['location_dest_id'][0], move['product_id'][0])
            incoming_dict[key] = incoming_dict.get(key, 0) + move['qty_done']

        outgoing_moves = self.env['stock.move.line'].read_group(domain_out,
                                                                ['product_id', 'location_id', 'qty_done:sum'],
                                                                ['product_id', 'location_id'], lazy=False)
        outgoing_dict = {}
        for move in outgoing_moves:
            key = (move['location_id'][0], move['product_id'][0])
            outgoing_dict[key] = outgoing_dict.get(key, 0) + move['qty_done']

        all_keys = set(initial_stock_dict.keys()) | set(incoming_dict.keys()) | set(outgoing_dict.keys())

        loc_ids = list(set([k[0] for k in all_keys]))
        prod_ids = list(set([k[1] for k in all_keys]))

        locations_obj = self.env['stock.location'].browse(loc_ids)
        products_obj = self.env['product.product'].browse(prod_ids).with_company(self.company_id)

        loc_dict = {l.id: l.name for l in locations_obj}
        prod_dict = {p.id: p for p in products_obj}

        record_list = []
        for loc_id, prod_id in all_keys:
            initial = initial_stock_dict.get((loc_id, prod_id), 0)
            in_qty = incoming_dict.get((loc_id, prod_id), 0)
            out_qty = outgoing_dict.get((loc_id, prod_id), 0)
            balance = initial + in_qty - out_qty

            if initial == 0 and in_qty == 0 and out_qty == 0 and balance == 0:
                continue

            product = prod_dict[prod_id]
            sale_price = round(float(product.list_price or 0.0), 2)
            cost_price = round(float(product.standard_price or 0.0), 2)

            record_list.append({
                'location_name': loc_dict[loc_id],
                'product': product.name,
                'default_code': product.default_code or '',
                'uom': product.uom_id.name,
                'hsn': product.product_tmpl_id.l10n_in_hsn_code or '',
                'initial_stock': initial,
                'in': in_qty,
                'out': out_qty,
                'balance': balance,
                'sale_price': sale_price,
                'sale_value': round(sale_price * balance, 2),
                'cost_price': cost_price,
                'cost_value': round(cost_price * balance, 2),
                'rec_set': product,
            })

        return sorted(record_list, key=lambda k: (k['location_name'], k['product']))

    def _calculate_totals(self, record_list):
        return {
            'initial_stock': sum(rec.get('initial_stock', 0) for rec in record_list),
            'in': sum(rec.get('in', 0) for rec in record_list),
            'out': sum(rec.get('out', 0) for rec in record_list),
            'balance': sum(rec.get('balance', 0) for rec in record_list),
            'sale_value': sum(rec.get('sale_value', 0) for rec in record_list),
            'cost_value': sum(rec.get('cost_value', 0) for rec in record_list),
        }

    def _calculate_category_totals(self, category_dict):
        category_totals = {}
        for category_name, records in category_dict.items():
            category_totals[category_name] = self._calculate_totals(records)
        return category_totals

    def _prepare_grouped_data(self, record_list):
        locations_data = {}
        location_totals = {}
        category_totals_by_loc = {}

        for loc_name in set(r['location_name'] for r in record_list):
            loc_recs = [r for r in record_list if r['location_name'] == loc_name]
            location_totals[loc_name] = self._calculate_totals(loc_recs)

            if self.group_by_category:
                cat_dict = {}
                for r in loc_recs:
                    cat_name = r['rec_set'].categ_id.name
                    cat_dict.setdefault(cat_name, []).append(r)
                locations_data[loc_name] = cat_dict
                category_totals_by_loc[loc_name] = self._calculate_category_totals(cat_dict)
            else:
                locations_data[loc_name] = loc_recs

        return locations_data, location_totals, category_totals_by_loc

    def button_export_pdf(self):
        if not self.start_date or not self.end_date:
            raise UserError(_("Please select both a Start Date and an End Date."))

        start_dt = datetime.combine(self.start_date, time.min)
        end_dt = datetime.combine(self.end_date, time.max)

        record_list = self._get_report_data(start_dt, end_dt)
        grand_totals = self._calculate_totals(record_list)
        locations_data, location_totals, category_totals_by_loc = self._prepare_grouped_data(record_list)

        locations_str = ', '.join(self.location_ids.mapped('name')) if self.location_ids else "All Locations"

        data = {
            'report_start_date': self.start_date,
            'report_end_date': self.end_date,
            'report_company_id': self.company_id.name,
            'report_location': locations_str,
            'total_initial_stock': grand_totals['initial_stock'],
            'total_in': grand_totals['in'],
            'total_out': grand_totals['out'],
            'total_balance': grand_totals['balance'],
            'total_sale_value': grand_totals['sale_value'],
            'total_cost_value': grand_totals['cost_value'],
            'report_group_by_category': self.group_by_category,
            'locations_data': locations_data,
            'location_totals': location_totals,
            'category_totals_by_loc': category_totals_by_loc,
        }

        return self.env.ref('stock_report_cr.action_report_stock_report').report_action(self, data=data)

    def button_export_xlsx(self):
        if not self.start_date or not self.end_date:
            raise UserError(_("Please select both a Start Date and an End Date."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Inventory Excel Report')

        start_dt = datetime.combine(self.start_date, time.min)
        end_dt = datetime.combine(self.end_date, time.max)

        record_list = self._get_report_data(start_dt, end_dt)
        grand_totals = self._calculate_totals(record_list)
        locations_data, location_totals, category_totals_by_loc = self._prepare_grouped_data(record_list)

        header_style = workbook.add_format({'bold': True, 'align': 'left'})
        date_style = workbook.add_format({'align': 'left', 'num_format': 'dd-mm-yyyy'})

        # Row styling for grouping
        loc_header_style = workbook.add_format({'bg_color': '#dbeafe', 'bold': True, 'align': 'left', 'font_size': 12})
        cat_header_style = workbook.add_format({'bg_color': '#f1f5f9', 'bold': True, 'align': 'left'})
        subtotal_style = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#f8fafc'})
        loc_total_style = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#e2e8f0'})
        total_style = workbook.add_format(
            {'bold': True, 'align': 'center', 'bg_color': '#10b981', 'font_color': 'white'})

        locations_str = ', '.join(self.location_ids.mapped('name')) if self.location_ids else "All Locations"

        # --- UPDATED TOP INFORMATION LAYOUT ---
        sheet.write(0, 0, 'Company:', header_style)
        sheet.write(0, 1, self.company_id.name, date_style)
        sheet.write(0, 3, 'Start Date:', header_style)
        sheet.write(0, 4, str(self.start_date), date_style)

        sheet.write(2, 0, 'Location Filter:', header_style)
        sheet.write(2, 1, locations_str, date_style)
        sheet.write(2, 3, 'End Date:', header_style)
        sheet.write(2, 4, str(self.end_date), date_style)

        # --- WIDER COLUMNS FIXED ---
        sheet.set_column('A:A', 15)  # Reference
        sheet.set_column('B:B', 38)  # Designation (Extra wide)
        sheet.set_column('C:D', 10)  # UoM, HSN
        sheet.set_column('E:L', 13)  # Initial Stock, Values, etc.

        head_style = workbook.add_format(
            {'align': 'center', 'bold': True, 'bg_color': '#1e3a8a', 'font_color': 'white'})
        data_font_style = workbook.add_format({'align': 'center'})
        data_left_style = workbook.add_format({'align': 'left'})

        row = 5
        # --- REMOVED LOCATION FROM TABLE HEADER ---
        headers = ['Reference', 'Designation', 'UoM', 'HSN', 'Initial stock', 'IN', 'OUT', 'Balance', 'Sale Price',
                   'Sale Value', 'Cost Price', 'Cost Value']
        for col_num, header in enumerate(headers):
            sheet.write(row, col_num, header, head_style)
        sheet.freeze_panes(6, 0)

        row = 6

        def _write_line(sheet, row, line):
            sheet.write(row, 0, line.get('default_code'), data_font_style)
            sheet.write(row, 1, line.get('product'), data_left_style)
            sheet.write(row, 2, line.get('uom'), data_font_style)
            sheet.write(row, 3, line.get('hsn'), data_font_style)
            sheet.write(row, 4, line.get('initial_stock'), data_font_style)
            sheet.write(row, 5, line.get('in'), data_font_style)
            sheet.write(row, 6, line.get('out'), data_font_style)
            sheet.write(row, 7, line.get('balance'), data_font_style)
            sheet.write(row, 8, line.get('sale_price'), data_font_style)
            sheet.write(row, 9, line.get('sale_value'), data_font_style)
            sheet.write(row, 10, line.get('cost_price'), data_font_style)
            sheet.write(row, 11, line.get('cost_value'), data_font_style)

        for loc_name, loc_data in locations_data.items():
            # Write Location Header Row
            sheet.merge_range(row, 0, row, 11, loc_name, loc_header_style)
            row += 1

            if self.group_by_category:
                for cat_name, recs in loc_data.items():
                    # Write Category Header Row
                    sheet.merge_range(row, 0, row, 11, f"  Category: {cat_name}", cat_header_style)
                    row += 1
                    for line in recs:
                        _write_line(sheet, row, line)
                        row += 1

                    # Category Subtotal
                    sheet.write(row, 0, 'Category Subtotal:', subtotal_style)
                    for i in range(1, 4): sheet.write(row, i, '', subtotal_style)
                    sheet.write(row, 4, category_totals_by_loc[loc_name][cat_name]['initial_stock'], subtotal_style)
                    sheet.write(row, 5, category_totals_by_loc[loc_name][cat_name]['in'], subtotal_style)
                    sheet.write(row, 6, category_totals_by_loc[loc_name][cat_name]['out'], subtotal_style)
                    sheet.write(row, 7, category_totals_by_loc[loc_name][cat_name]['balance'], subtotal_style)
                    sheet.write(row, 8, '', subtotal_style)
                    sheet.write(row, 9, category_totals_by_loc[loc_name][cat_name]['sale_value'], subtotal_style)
                    sheet.write(row, 10, '', subtotal_style)
                    sheet.write(row, 11, category_totals_by_loc[loc_name][cat_name]['cost_value'], subtotal_style)
                    row += 1
            else:
                for line in loc_data:
                    _write_line(sheet, row, line)
                    row += 1

            # Location Subtotal
            sheet.write(row, 0, 'Total', loc_total_style)
            for i in range(1, 4): sheet.write(row, i, '', loc_total_style)
            sheet.write(row, 4, location_totals[loc_name]['initial_stock'], loc_total_style)
            sheet.write(row, 5, location_totals[loc_name]['in'], loc_total_style)
            sheet.write(row, 6, location_totals[loc_name]['out'], loc_total_style)
            sheet.write(row, 7, location_totals[loc_name]['balance'], loc_total_style)
            sheet.write(row, 8, '', loc_total_style)
            sheet.write(row, 9, location_totals[loc_name]['sale_value'], loc_total_style)
            sheet.write(row, 10, '', loc_total_style)
            sheet.write(row, 11, location_totals[loc_name]['cost_value'], loc_total_style)
            row += 2

        # Grand Total
        sheet.write(row, 0, 'GRAND TOTAL:', total_style)
        for i in range(1, 4): sheet.write(row, i, '', total_style)
        sheet.write(row, 4, grand_totals['initial_stock'], total_style)
        sheet.write(row, 5, grand_totals['in'], total_style)
        sheet.write(row, 6, grand_totals['out'], total_style)
        sheet.write(row, 7, grand_totals['balance'], total_style)
        sheet.write(row, 8, '', total_style)
        sheet.write(row, 9, grand_totals['sale_value'], total_style)
        sheet.write(row, 10, '', total_style)
        sheet.write(row, 11, grand_totals['cost_value'], total_style)

        workbook.close()
        xlsx_data = output.getvalue()
        self.xls_file = base64.encodebytes(xlsx_data)
        self.xls_filename = "Stock Excel Report.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'name': 'Inventory Excel Report',
            'url': '/web/content/stock.reports/%s/xls_file/%s?download=true' % (self.id, 'Stock Excel Report.xlsx'),
        }
