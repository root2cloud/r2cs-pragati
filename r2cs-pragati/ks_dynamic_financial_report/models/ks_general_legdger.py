from odoo import models

class KsDynamicFinancialBaseInherit(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def ks_get_df_report_data(self, filters):
        res = super(KsDynamicFinancialBaseInherit, self).ks_get_df_report_data(filters)

        # If SQL already provides move_state, just normalize it
        if 'account_data' in res and res['account_data']:
            for line in res['account_data']:
                if 'move_state' in line:
                    line['move_state'] = (line['move_state'] or '').upper()

        elif 'data' in res and isinstance(res['data'], list):
            for section in res['data']:
                if isinstance(section, dict) and 'account_data' in section:
                    for line in section['account_data']:
                        if 'move_state' in line:
                            line['move_state'] = (line['move_state'] or '').upper()

        return res
