from odoo import models, fields, api
from datetime import datetime, timedelta

class ServiceOrder(models.Model):
    _inherit = 'service.order'

    # Define the One2many relation if not already present
    # completion_ids = fields.One2many(
    #     'service.completion',
    #     'service_order_id',  # <- This must match the field in service.completion
    #     string='Completions'
    # )

    complete_date = fields.Date(
        string='Completion Date',
        compute='_compute_complete_date',
        store=True
    )



    complete_delay_days = fields.Integer(
        string="Completion Delay (Days)",
        compute="_compute_days",
        store=True
    )

    completion_ids = fields.One2many('service.completion', 'service_order_id', string='Service Completions')

    service_completion_numbers = fields.Char(
        string='Service Completion Numbers',
        compute='_compute_completion_numbers',
        store=False,  # No need to store, just display
        readonly=True
    )

    completion_statuses = fields.Char(
        string='Service Completion Statuses',
        compute='_compute_completion_statuses',
        store=False,
        readonly=True
    )



    # service_completion_number = fields.Char(
    #     string='Service Completion Number',
    #     compute='_compute_service_completion_number',
    #     store=True,
    #     readonly=True
    # )


    @api.depends('completion_ids.complete_date')
    def _compute_complete_date(self):
        for record in self:
            dates = record.completion_ids.mapped('complete_date')
            record.complete_date = max(dates) if dates else False

    @api.depends('expect_arrival', 'complete_date')
    def _compute_days(self):
        for order in self:
            if order.expect_arrival and order.complete_date:
                # Convert datetime to date before subtracting
                expect_date = order.expect_arrival.date() if hasattr(order.expect_arrival,
                                                                     'date') else order.expect_arrival
                order.complete_delay_days = (order.complete_date - expect_date).days
            else:
                order.complete_delay_days = 0

    @api.depends('completion_ids.name')
    def _compute_completion_numbers(self):
        for order in self:
            names = order.completion_ids.mapped('name')
            order.service_completion_numbers = ', '.join(names)

    @api.depends('completion_ids.state')  # <-- use the correct field
    def _compute_completion_statuses(self):
        for order in self:
            statuses = order.completion_ids.mapped('state')  # Get states from linked completions
            unique_statuses = list(set(statuses))  # Remove duplicates
            order.completion_statuses = ', '.join(unique_statuses) if unique_statuses else 'No completions'
# def _compute_days(self):
    #     for order in self:
    #         if order.expect_arrival and order.complete_date:
    #             order.complete_delay_days = (order.complete_date - order.expect_arrival).days
    #         else:
    #             order.complete_delay_days = 0
