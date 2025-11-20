from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to check for duplicate contact names and auto-generate payable accounts"""

        for vals in vals_list:
            if vals.get('name'):
                existing_partner = self.search(
                    [('name', '=', vals['name'])],
                    limit=1
                )

                if existing_partner:
                    raise ValidationError(
                        f"Contact with name '{vals['name']}' already exists. "
                        f"Please use a unique name."
                    )

        # Create partners after validation
        partners = super().create(vals_list)

        for partner in partners:
            try:
                if partner.name:
                    self._create_partner_payable_account(partner)
            except Exception as e:
                _logger.error(f"Error creating payable account for {partner.name}: {str(e)}")

        return partners

    def _create_partner_payable_account(self, partner):
        """Create payable account with partner name"""
        account_account = self.env['account.account']

        # Get company
        company = partner.company_id or self.env.company

        # Generate unique account code
        payable_code = self._get_next_account_code(company)

        try:
            # Create Payable Account with partner name
            payable_account_vals = {
                'code': payable_code,
                'name': partner.name,
                'account_type': 'liability_payable',
                'company_id': company.id,
            }
            payable_account = account_account.create(payable_account_vals)

            # Assign this account to the contact's Account Payable field
            partner.property_account_payable_id = payable_account.id
            _logger.info(f"Created payable account '{partner.name}' (Code: {payable_code})")

        except Exception as e:
            _logger.error(f"Failed to create payable account for {partner.name}: {str(e)}")
            raise ValidationError(f"Error creating payable account: {str(e)}")

    def _get_next_account_code(self, company):
        """Generate next unique account code"""
        account_account = self.env['account.account']

        # Find the last account by code
        last_account = account_account.search(
            [('company_id', '=', company.id)],
            order='code desc',
            limit=1
        )

        if last_account and last_account.code:
            try:
                next_code = int(last_account.code) + 1
                return str(next_code).zfill(6)
            except ValueError:
                return last_account.code + '1'

        return '100001'  # Default starting code
