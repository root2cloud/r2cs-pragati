from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)

class MrpCheck(models.Model):
    _name = 'mrp.check'
    _description = 'MRP Check'

    name = fields.Char(string='Check Name', required=True)
    quality_state = fields.Selection(
        [
            ('none', 'None'),
            ('pass', 'Passed'),
            ('fail', 'Failed')
        ],
        string='Quality State',
        default='none'
    )
    test_type = fields.Selection(
        [
            ('dimensional', 'Dimensional'),
            ('functional', 'Functional'),
            ('visual', 'Visual'),
            ('destructive', 'Destructive')
        ],
        string='Test Type'
    )

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order')

    description = fields.Text(string='Description')


_logger.info(">>>>>>>> mrp.check model loaded successfully <<<<<<<<")
