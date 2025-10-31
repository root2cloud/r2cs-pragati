from odoo import models, fields, api

class LocationType(models.Model):
	_name = 'location.type'
	_description = 'Location Types for the Net Houses'

	name = fields.Char(string='Location type')