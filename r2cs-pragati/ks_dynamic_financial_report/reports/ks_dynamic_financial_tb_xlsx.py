# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import xlsxwriter
import json
import collections
import datetime
import io


class KsDynamicFinancialXlsxTB(models.Model):
    _inherit = 'ks.dynamic.financial.base'

    def ks_get_xlsx_trial_balance(self, ks_df_informations):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        row_pos = 0
        lang = self.env.user.lang
        lang_id = self.env['res.lang'].search([('code', '=', lang)])['date_format'].replace('/', '-')

        # Get company and date information
        company_id = ks_df_informations.get('company_id')

        # Handle different date scenarios
        date_info = self._get_date_range(ks_df_informations)
        start_date = date_info['start_date']
        end_date = date_info['end_date']
        period_name = date_info['period_name']

        # Build trial balance data with enhanced grouping structure
        move_lines = self._build_complete_trial_balance_with_enhanced_groups(company_id, start_date, end_date)

        ks_company_id = self.env['res.company'].sudo().browse(company_id)
        sheet = workbook.add_worksheet('Trial_balance')

        # Set column widths for 8-column structure
        sheet.set_column(0, 0, 35)  # Particulars
        sheet.set_column(1, 1, 12)  # Code
        sheet.set_column(2, 2, 15)  # Opening Balance Dr
        sheet.set_column(3, 3, 15)  # Opening Balance Cr
        sheet.set_column(4, 4, 18)  # Debits for the period
        sheet.set_column(5, 5, 18)  # Credits for the period
        sheet.set_column(6, 6, 15)  # Closing Balance Dr
        sheet.set_column(7, 7, 15)  # Closing Balance Cr
        sheet.set_column(8, 8, 25)  # Main Group
        sheet.set_column(9, 9, 20)  # Sub Group
        sheet.set_column(10, 10, 30)  # Sub-Sub Group

        # Define formats
        format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 12,
            'font': 'Arial',
            'bg_color': '#4472C4',
            'font_color': 'white'
        })

        format_company = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 11,
            'font': 'Arial',
        })

        format_header = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'font': 'Arial',
            'align': 'center',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'text_wrap': True
        })

        line_header_light_left = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'left',
            'font': 'Arial',
            'border': 1
        })

        line_header_light_center = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'border': 1
        })

        line_header_light_right = workbook.add_format({
            'bold': False,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'border': 1,
            'num_format': '#,##0.00'
        })

        # Total row format
        format_total = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'right',
            'font': 'Arial',
            'border': 1,
            'num_format': '#,##0.00',
            'bg_color': '#E7E6E6'
        })

        format_total_text = workbook.add_format({
            'bold': True,
            'font_size': 10,
            'align': 'center',
            'font': 'Arial',
            'border': 1,
            'bg_color': '#E7E6E6'
        })

        # Date formatting
        ks_new_start_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d').date()).strftime('%d/%m/%Y')
        ks_new_end_date = (datetime.datetime.strptime(end_date, '%Y-%m-%d').date()).strftime('%d/%m/%Y')

        # Company name and title with period information
        title_text = f"{ks_company_id.name.upper()}"
        sheet.merge_range(row_pos, 0, row_pos, 10, title_text, format_company)
        row_pos += 1

        sheet.merge_range(row_pos, 0, row_pos, 10, "Trial balance", format_company)
        row_pos += 2

        if period_name == "Custom Date Range":
            period_text = f"[Custom Range ({ks_new_start_date} to {ks_new_end_date})]"
        else:
            period_text = f"[{period_name}]"
        sheet.merge_range(row_pos, 0, row_pos, 10, period_text, format_company)
        row_pos += 2

        # Multi-level column headers
        # First level headers
        sheet.merge_range(row_pos, 0, row_pos + 1, 0, 'Particulars', format_header)
        sheet.merge_range(row_pos, 1, row_pos + 1, 1, 'Code', format_header)
        sheet.merge_range(row_pos, 2, row_pos, 3, 'Opening Balance', format_header)
        sheet.merge_range(row_pos, 4, row_pos, 5, 'Transaction', format_header)
        sheet.merge_range(row_pos, 6, row_pos, 7, 'Closing Balance', format_header)
        sheet.merge_range(row_pos, 8, row_pos + 1, 8, 'Main Group', format_header)
        sheet.merge_range(row_pos, 9, row_pos + 1, 9, 'Sub Group', format_header)
        sheet.merge_range(row_pos, 10, row_pos + 1, 10, 'Sub-Sub Group', format_header)
        row_pos += 1

        # Second level headers
        sheet.write_string(row_pos, 2, 'Dr (Op bal)', format_header)
        sheet.write_string(row_pos, 3, 'Cr (Op bal)', format_header)
        sheet.write_string(row_pos, 4, 'Debits for the period', format_header)
        sheet.write_string(row_pos, 5, 'Credits for the period', format_header)
        sheet.write_string(row_pos, 6, 'Dr (YTD)', format_header)
        sheet.write_string(row_pos, 7, 'Cr (YTD)', format_header)
        row_pos += 1

        # Enhanced function to get account group hierarchy based on exact Excel data
        def get_account_group_hierarchy(account_code, account_name=""):
            """
            Returns a dictionary with the complete hierarchy based on your exact Excel structure and corrected mismatches
            """
            if not account_code:
                return {
                    'main_group': 'OTHER',
                    'sub_group': 'Miscellaneous',
                    'sub_sub_group': 'Other Accounts'
                }

            try:
                code_str = str(account_code).strip()
                name_lower = str(account_name).lower()

                # Handle specific account names first for exact matches - CORRECTED BASED ON YOUR EXCEL

                # TDS Interest accounts - CORRECTED
                if any(keyword in name_lower for keyword in ['interest on tds', 'interest on tds late payment',
                                                             'interest on tds late payments']):
                    return {
                        'main_group': 'EXPENSES',
                        'sub_group': 'Indirect Expenses',
                        'sub_sub_group': 'Statutory Payments - TDS'
                    }

                # Unloading Charges - CORRECTED
                elif 'unloading charges' in name_lower:
                    return {
                        'main_group': 'EXPENSES',
                        'sub_group': 'Indirect Expenses',
                        'sub_sub_group': 'Transport Charges'
                    }

                # Interest on Vardhaman Bank - CORRECTED
                elif 'interest on vardhaman' in name_lower:
                    return {
                        'main_group': 'EXPENSES',
                        'sub_group': 'Indirect Expenses',
                        'sub_sub_group': 'FINANCE COST'
                    }

                # Vardhaman Bank Current Account - CORRECTED
                elif 'vardhaman mahila co op urban bank' in name_lower and 'ca a/c' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Bank Accounts'
                    }

                # Employee E5008-Jhansi T - CORRECTED
                elif 'e5008-jhansi t' in name_lower or 'jhansi t' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Employee Salary Advance'
                    }

                # SHIVAPARVATIY - CORRECTED to Resort Sparsh
                elif 'shivaparvatiy' in name_lower or 'shivaparvatoy' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Resort Sparsh'
                    }

                # DR. M. BABAIAH - CORRECTED to Resort Sparsh
                elif 'dr. m. babaiah' in name_lower or 'dr.m.babaiah' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Resort Sparsh'
                    }

                # Dr. NAGARAJU - CORRECTED to Resort Sparsh
                elif 'dr. nagaraju' in name_lower or 'dr.nagaraju' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Resort Sparsh'
                    }

                # R.V.Subba Rao(Consultant) - CORRECTED to Resort Sparsh
                elif 'r.v.subba rao' in name_lower and 'consultant' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Resort Sparsh'
                    }

                # Dr.Saryanan - CORRECTED to Sparsh MP
                elif 'dr.saryanan' in name_lower or 'dr. saryanan' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Sparsh MP'
                    }

                # Pragati Green Meadows & Resorts(Share Capital) - CORRECTED
                elif 'pragati green meadows' in name_lower and 'share capital' in name_lower:
                    return {
                        'main_group': 'Equity',
                        'sub_group': 'Capital Accounts',
                        'sub_sub_group': 'Equity Share Capital'
                    }

                # Unamortised Expenses
                elif 'unamortised expenses' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Non - Current Asset',
                        'sub_sub_group': 'OTHER NON CURRENT ASSESTS'
                    }

                # Prepaid Insurance
                elif 'prepaid insurance' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Prepaid Expenses',
                        'sub_sub_group': 'OTHER NON CURRENT ASSESTS'
                    }

                # Investment in Vardhaman Bank
                elif 'investment in vardhaman bank' in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Non - Current Asset',
                        'sub_sub_group': 'Deposits'
                    }

                # Deferred Tax
                elif 'deferred tax' in name_lower or 'defferred tax' in name_lower:
                    return {
                        'main_group': 'LIABILITIES',
                        'sub_group': 'Non-Current Liability',
                        'sub_sub_group': 'DEFERRED TAX LIABILITY'
                    }

                # Registration Fee
                elif 'registration fee' in name_lower:
                    return {
                        'main_group': 'REVENUE',
                        'sub_group': 'Revenue From Operations',
                        'sub_sub_group': 'Sale of Products/Services'
                    }

                # Other Group Company Investments (NOT share capital ones)
                elif any(company in name_lower for company in ['pragati green meadows', 'pragati dwellers',
                                                               'pragati multi-tech', 'pragati green avenue',
                                                               'gaddipati trust', 'pgm real estate',
                                                               'pgm homes india', 'pragati prakruthi matha',
                                                               'pgm builders company']) and 'share capital' not in name_lower:
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Non - Current Asset',
                        'sub_sub_group': 'Investment in Group companies'
                    }

                # Employee related accounts starting with E (general pattern)
                elif (code_str.startswith('E') or 'e5' in code_str.lower() or 'e1' in code_str.lower()) and \
                        not any(name in name_lower for name in ['dr. m. babaiah', 'dr. nagaraju', 'r.v.subba rao']):
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Employee Salary Advance'
                    }

                # Staff Welfare and related expenses
                elif any(keyword in name_lower for keyword in
                         ['staff welfare', 'salaries & wages -f&f', 'leave encashment']):
                    return {
                        'main_group': 'EXPENSES',
                        'sub_group': 'Indirect Expenses',
                        'sub_sub_group': 'Staff Welfare' if 'staff welfare' in name_lower else 'Salaries & Allowances'
                    }

                # Resort customers (not already covered above)
                elif any(name in name_lower for name in ['savithri', 'uma saraswathi', 'd.venkateswar reddy',
                                                         'premchand-new', 'hrudai', 'harpreet kaur',
                                                         'narsimham srivari', 'swati',
                                                         'deen dayal khandelwal', 'pushpa gupta',
                                                         'ambati murali krishna', 'srinivas pathakota',
                                                         'mr. srinivas', 'k.venkatesh', 'annapurna',
                                                         'p.sujatha', 'naidu narayana reddy', 'laxhmi devineni',
                                                         'k ravi kama raju', 'agarwal ramesh', 'mr.srinivas',
                                                         'vijaya', 'vita sana integrative']):
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Resort Sparsh'
                    }

                # MP customers (not already covered above)
                elif any(name in name_lower for name in ['b.sreedevi', 'g.china venkata rao', 'kalvakolanu aparna',
                                                         'swapna', 'mr. k.v.kumar']):
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Sundry Debtors Sparsh MP'
                    }

                # Other Employee advances (not already covered above)
                elif any(name in name_lower for name in ['kanaka babu-watchman', 'satyanarayana-pbpl',
                                                         'shanker therapist', 'e5039-ravi teja.p(a&e)',
                                                         'e1951-suresh kotha', 'n.n.acharyulu', 'vasavi chilla']):
                    return {
                        'main_group': 'ASSETS',
                        'sub_group': 'Current Assets',
                        'sub_sub_group': 'Employee Salary Advance'
                    }

                # Suppliers that should be creditors
                elif any(name in name_lower for name in ['lotus leaf organic', 'chemiloids life sciences',
                                                         'jasper industries', 'mukesh', 'sri bhagavathi ayurvedic',
                                                         'amrutaaharam', 'ficus life sciences', 'sami-sabinsa',
                                                         'razorpay software']):
                    return {
                        'main_group': 'LIABILITIES',
                        'sub_group': 'Current Liability',
                        'sub_sub_group': 'Sundry Creditors'
                    }

                # Handle specific codes based on your Excel data
                if code_str.isdigit():
                    code_num = int(code_str)

                    # Staff Welfare accounts (100211, 100212, 100213)
                    if code_num in [100211, 100212, 100213]:
                        return {
                            'main_group': 'EXPENSES',
                            'sub_group': 'Indirect Expenses',
                            'sub_sub_group': 'Staff Welfare'
                        }

                    # Bank accounts (500202, 500203, 500205)
                    elif code_num in [500202, 500203, 500205]:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'Bank Accounts'
                        }

                    # Employee Salary Advance - Specific codes
                    elif code_num in [600252, 600253, 600254, 600255, 600256, 600257, 600258, 600259,
                                      600270, 600271, 600325, 600348, 600349, 600357, 600358, 600360,
                                      600361, 600377, 600385, 600387]:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'Employee Salary Advance'
                        }

                    # Investment in Group Companies (600502)
                    elif code_num == 600502:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Non - Current Asset',
                            'sub_sub_group': 'Investment in Group Companies'
                        }

                    # Deferred Tax Expense (700003)
                    elif code_num == 700003:
                        return {
                            'main_group': 'EXPENSES',
                            'sub_group': 'Indirect Expenses',
                            'sub_sub_group': 'Deferred Tax Expense'
                        }

                    # Unsecured Loans from Related Parties (700051, 700052, 700053)
                    elif code_num in [700051, 700052, 700053]:
                        return {
                            'main_group': 'LIABILITIES',
                            'sub_group': 'Non - Current Liability',
                            'sub_sub_group': 'Unsecured Loans from Related Parties'
                        }

                    # Share Capital accounts (700072-700076)
                    elif code_num in [700072, 700073, 700074, 700075]:
                        return {
                            'main_group': 'Equity',
                            'sub_group': 'Capital Accounts',
                            'sub_sub_group': 'Equity Share Capital'
                        }

                    # Profit & Loss accounts (700071, 700076)
                    elif code_num in [700071, 700076]:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Control Account',
                            'sub_sub_group': 'Profit & Loss Account'
                        }

                    # Bank accounts (general range with bank keyword)
                    elif (500200 <= code_num <= 500299) and ('bank' in name_lower):
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'Bank Accounts'
                        }

                    # Cash accounts (500201, 500208, 500212-500222, 100133)
                    elif (500200 <= code_num <= 500299 and 'cash' in name_lower) or code_num == 100133:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'Cash In Hand'
                        }

                    # Cash Difference accounts (400210, 300233)
                    elif code_num in [400210, 300233]:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'Cash In Hand'
                        }

                    # Closing Stock (100101, 600646)
                    elif code_num == 100101 or (code_num == 600646 and 'closing stock' in name_lower):
                        if code_num == 600646:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Changes In Inventory',
                                'sub_sub_group': 'CLOSING STOCK P/L'
                            }
                        else:
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Current Assets',
                                'sub_sub_group': 'Inventories'
                            }

                    # Opening Stock (300226)
                    elif code_num == 300226:
                        return {
                            'main_group': 'EXPENSES',
                            'sub_group': 'Changes In Inventory',
                            'sub_sub_group': 'OPENING STOCK P&L'
                        }

                    # WIP-BS (100102)
                    elif code_num == 100102:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'Inventories'
                        }

                    # Paytm & Razorpay (500101-500105, 600640)
                    elif (500101 <= code_num <= 500105) or code_num == 600640:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Current Assets',
                            'sub_sub_group': 'PAYTM & Razorpay Collection'
                        }

                    # Outstanding/Suspense accounts (100123-100201, 1002010, 500223, 600260)
                    elif code_num in [100123, 100124, 100126, 100128, 100149, 100201, 1002010, 500223, 600260]:
                        return {
                            'main_group': 'LIABILITIES',
                            'sub_group': 'Current Liability',
                            'sub_sub_group': 'Other Creditors'
                        }

                    # Provision for Expenses (200701-200708, 600277, 200702, 300352, 600363)
                    elif (200701 <= code_num <= 200708) or code_num in [600277, 200702, 300352, 600363]:
                        return {
                            'main_group': 'LIABILITIES',
                            'sub_group': 'Current Liability',
                            'sub_sub_group': 'Provision for Expenses'
                        }

                    # Fixed Assets based on codes (100302-100327)
                    elif 100302 <= code_num <= 100327:
                        if code_num == 100318:  # Computer Peripheral
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Computers'
                            }
                        elif code_num in [100303, 100308, 100310]:  # Electrical Equipment
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'ELECTRICAL EQUIPMENT'
                            }
                        elif code_num in [100307, 100324, 100325]:  # Furniture & Fixtures
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Furniture & Fixture'
                            }
                        elif code_num in [100313, 100327]:  # Intangible Assets
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Intangible Asset'
                            }
                        elif code_num == 100311:  # Lab Equipment
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'LAB EQUIPMENT'
                            }
                        elif code_num == 100302:  # Land
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Land Asset'
                            }
                        elif code_num == 100319:  # Office Equipment
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Office Equipments'
                            }
                        elif code_num == 100309:  # Other Assets
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Other Assets'
                            }
                        elif code_num == 100312:  # Depreciation
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Provision for Depriciation'
                            }
                        elif code_num in [100305, 100314, 100316, 100317]:  # Vehicles
                            return {
                                'main_group': 'ASSETS',
                                'sub_group': 'Fixed Assets',
                                'sub_sub_group': 'Vehicles'
                            }

                    # Indirect Expenses (300xxx range) - Enhanced mappings
                    elif 300200 <= code_num <= 300400:
                        if any(keyword in name_lower for keyword in ['website', 'business promotion', 'advertisement']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Advertisment & Business Promotion'
                            }
                        elif any(keyword in name_lower for keyword in ['agriculture', 'farm', 'plants']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Agriculture Expenses'
                            }
                        elif 'audit' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Audit Charges & Expenses'
                            }
                        elif 'civil' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Civil Work Expenses'
                            }
                        elif any(keyword in name_lower for keyword in ['commission', 'brokerage']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Commission & Brokerage'
                            }
                        elif any(keyword in name_lower for keyword in ['computer', 'software', 'laptop']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Computers & Software Maintainance'
                            }
                        elif 'depreciation' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Depreciation'
                            }
                        elif 'donation' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Donation'
                            }
                        elif any(keyword in name_lower for keyword in ['electricity', 'water', 'power']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Electricity, Power & Water'
                            }
                        elif any(keyword in name_lower for keyword in ['salary', 'wages', 'bonus']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Salaries & Allowances'
                            }
                        elif 'rent' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Rent'
                            }
                        elif any(keyword in name_lower for keyword in ['travelling', 'conveyance']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Travelling & Conveyance'
                            }
                        elif 'printing & stationery' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Priting & Stationery'
                            }
                        elif any(keyword in name_lower for keyword in ['repairing expense', 'repairs & maintenance']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Repairs &Maintenance'
                            }
                        elif 'consultancy charges' in name_lower or 'consultation fees' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Professional & Consultancy Charges'
                            }
                        elif 'p f administrative charges' in name_lower or 'pf employer contribution' in name_lower or 'esi employer contribution' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Statutory Payments - PF ESI'
                            }
                        elif 'subscription & membership fee' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'General Expenses-'
                            }
                        elif any(keyword in name_lower for keyword in ['vehicle maintenance', 'office maintenance']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Repairs &Maintenance'
                            }
                        elif 'surgical equipment' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Direct Expenses',
                                'sub_sub_group': 'Purchases of Products/Raw Materials'
                            }
                        elif 'insurance' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Insurance'
                            }
                        elif any(keyword in name_lower for keyword in ['internet charges', 'telephone charges']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Postage, Telephone & Internet'
                            }
                        elif 'income tax expenses' in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'IncomeTax'
                            }
                        elif any(keyword in name_lower for keyword in
                                 ['gst late fee', 'cgst penal charges', 'sgst penal charges']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Statutory Payments - GST'
                            }
                        elif any(keyword in name_lower for keyword in ['trade mark license', 'rates & taxes']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Statutory Payments - Others'
                            }
                        elif any(keyword in name_lower for keyword in
                                 ['transport', 'freight', 'hamali', 'delivery', 'courier']):
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Transport Charges'
                            }
                        elif any(keyword in name_lower for keyword in
                                 ['bank charges', 'interest', 'penalty', 'payment gate']) and \
                                'interest on tds' not in name_lower and 'interest on vardhaman' not in name_lower:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'FINANCE COST'
                            }
                        else:
                            return {
                                'main_group': 'EXPENSES',
                                'sub_group': 'Indirect Expenses',
                                'sub_sub_group': 'Other Expenses'
                            }

                    # Direct Expenses - Purchases (300xxx range for purchases)
                    elif (300200 <= code_num <= 300299) and any(
                            keyword in name_lower for keyword in
                            ['purchase', 'gas', 'therapy', 'stock', 'material']) and \
                            'unloading charges' not in name_lower:
                        return {
                            'main_group': 'EXPENSES',
                            'sub_group': 'Direct Expenses',
                            'sub_sub_group': 'Purchases of Products/Raw Materials'
                        }

                    # Loans & Borrowings (500216, 700001, 700002)
                    elif code_num in [500216, 700001, 700002]:
                        return {
                            'main_group': 'LIABILITIES',
                            'sub_group': 'Loans & Borrowings',
                            'sub_sub_group': 'Short Term Borrowings'
                        }

                    # Interest Income (100105, 400219, 600645)
                    elif code_num in [100105, 400219, 600645]:
                        return {
                            'main_group': 'REVENUE',
                            'sub_group': 'Non - Operating Revenue',
                            'sub_sub_group': 'Interest Income'
                        }

                    # Other Income (400220-400223)
                    elif 400220 <= code_num <= 400223:
                        return {
                            'main_group': 'REVENUE',
                            'sub_group': 'Non - Operating Revenue',
                            'sub_sub_group': 'Other Income'
                        }

                    # Deposits (100106-100109, 100326)
                    elif code_num in [100106, 100107, 100108, 100109, 100326]:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Non - Current Asset',
                            'sub_sub_group': 'Deposits'
                        }

                    # GST Input (100151-100158)
                    elif 100151 <= code_num <= 100158:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Other Current Asset',
                            'sub_sub_group': 'Input GST'
                        }

                    # GST Output (200751-200757)
                    elif 200751 <= code_num <= 200757:
                        return {
                            'main_group': 'LIABILITIES',
                            'sub_group': 'SHORT TERM PROVISION',
                            'sub_sub_group': 'Output GST'
                        }

                    # TDS Payable (200762-200773)
                    elif 200762 <= code_num <= 200773:
                        return {
                            'main_group': 'LIABILITIES',
                            'sub_group': 'SHORT TERM PROVISION',
                            'sub_sub_group': 'TDS Payable'
                        }

                    # TDS Receivable (100103, 100145, 100150)
                    elif code_num in [100103, 100145, 100150]:
                        return {
                            'main_group': 'ASSETS',
                            'sub_group': 'Other Current Asset',
                            'sub_sub_group': 'Advance Income Tax (Incl.TDS Receivables)'
                        }

                    # General Sundry Debtors/Creditors classification based on code ranges
                    elif (600504 <= code_num <= 600999):
                        # Skip specific named accounts already handled above
                        if not any(keyword in name_lower for keyword in ['salary', 'advance', 'employee', 'e5', 'e1',
                                                                         'dr.', 'shivaparvatiy', 'babaiah', 'nagaraju',
                                                                         'subba rao', 'saryanan']):
                            if any(keyword in name_lower for keyword in ['purchase', 'sale', 'revenue']):
                                if 'purchase' in name_lower:
                                    return {
                                        'main_group': 'EXPENSES',
                                        'sub_group': 'Direct Expenses',
                                        'sub_sub_group': 'Purchases of Products/Raw Materials'
                                    }
                                else:
                                    return {
                                        'main_group': 'REVENUE',
                                        'sub_group': 'Revenue From Operations',
                                        'sub_sub_group': 'Sale of Products/Services'
                                    }
                            else:
                                return {
                                    'main_group': 'LIABILITIES',
                                    'sub_group': 'Current Liability',
                                    'sub_sub_group': 'Sundry Creditors'
                                }

                # Default fallback - only for truly unrecognized codes
                return {
                    'main_group': 'OTHER',
                    'sub_group': 'Miscellaneous',
                    'sub_sub_group': 'Other Accounts'
                }

            except (ValueError, TypeError, AttributeError):
                return {
                    'main_group': 'OTHER',
                    'sub_group': 'Miscellaneous',
                    'sub_sub_group': 'Other Accounts'
                }

        # Function to check if account has any non-zero balance
        def has_non_zero_balance(line_data):
            return (
                    float(line_data.get('initial_debit', 0)) != 0 or
                    float(line_data.get('initial_credit', 0)) != 0 or
                    float(line_data.get('debit', 0)) != 0 or
                    float(line_data.get('credit', 0)) != 0 or
                    float(line_data.get('ending_debit', 0)) != 0 or
                    float(line_data.get('ending_credit', 0)) != 0
            )

        # Filter out accounts with all zero balances
        filtered_move_lines = {
            line_id: line_data
            for line_id, line_data in move_lines.items()
            if has_non_zero_balance(line_data)
        }

        # Sort filtered move_lines by account code
        sorted_move_lines = sorted(filtered_move_lines.items(), key=lambda x: x[1].get('code', ''))

        # Initialize totals
        total_opening_dr = 0.0
        total_opening_cr = 0.0
        total_period_dr = 0.0
        total_period_cr = 0.0
        total_closing_dr = 0.0
        total_closing_cr = 0.0

        # Process individual account lines
        for line_id, line in sorted_move_lines:
            account_name = line.get('name', '')
            account_code = line.get('code', '')

            # Skip if no account code
            if not account_code:
                continue

            # Get enhanced group hierarchy
            group_hierarchy = get_account_group_hierarchy(account_code, account_name)

            # Calculate closing balances properly
            opening_dr = float(line.get('initial_debit', 0))
            opening_cr = float(line.get('initial_credit', 0))
            period_dr = float(line.get('debit', 0))
            period_cr = float(line.get('credit', 0))

            # Calculate closing balance
            total_dr = opening_dr + period_dr
            total_cr = opening_cr + period_cr

            # Net closing balance
            closing_dr = max(0, total_dr - total_cr)
            closing_cr = max(0, total_cr - total_dr)

            # Add to totals
            total_opening_dr += opening_dr
            total_opening_cr += opening_cr
            total_period_dr += period_dr
            total_period_cr += period_cr
            total_closing_dr += closing_dr
            total_closing_cr += closing_cr

            # Write account details with all columns
            sheet.write_string(row_pos, 0, account_name, line_header_light_left)  # Particulars
            sheet.write_string(row_pos, 1, str(account_code), line_header_light_center)  # Code
            sheet.write_number(row_pos, 2, opening_dr, line_header_light_right)  # Opening Dr
            sheet.write_number(row_pos, 3, opening_cr, line_header_light_right)  # Opening Cr
            sheet.write_number(row_pos, 4, period_dr, line_header_light_right)  # Period Dr
            sheet.write_number(row_pos, 5, period_cr, line_header_light_right)  # Period Cr
            sheet.write_number(row_pos, 6, closing_dr, line_header_light_right)  # Closing Dr
            sheet.write_number(row_pos, 7, closing_cr, line_header_light_right)  # Closing Cr
            sheet.write_string(row_pos, 8, group_hierarchy['main_group'], line_header_light_left)  # Main Group
            sheet.write_string(row_pos, 9, group_hierarchy['sub_group'], line_header_light_left)  # Sub Group
            sheet.write_string(row_pos, 10, group_hierarchy['sub_sub_group'], line_header_light_left)  # Sub-Sub Group
            row_pos += 1

        # Add TOTAL row
        sheet.write_string(row_pos, 0, 'TOTAL', format_total_text)  # Particulars
        sheet.write_string(row_pos, 1, '', format_total_text)  # Code (empty)
        sheet.write_number(row_pos, 2, total_opening_dr, format_total)  # Total Opening Dr
        sheet.write_number(row_pos, 3, total_opening_cr, format_total)  # Total Opening Cr
        sheet.write_number(row_pos, 4, total_period_dr, format_total)  # Total Period Dr
        sheet.write_number(row_pos, 5, total_period_cr, format_total)  # Total Period Cr
        sheet.write_number(row_pos, 6, total_closing_dr, format_total)  # Total Closing Dr
        sheet.write_number(row_pos, 7, total_closing_cr, format_total)  # Total Closing Cr
        sheet.write_string(row_pos, 8, '', format_total_text)  # Main Group (empty)
        sheet.write_string(row_pos, 9, '', format_total_text)  # Sub Group (empty)
        sheet.write_string(row_pos, 10, '', format_total_text)  # Sub-Sub Group (empty)

        workbook.close()
        output.seek(0)
        generated_file = output.read()
        output.close()

        return generated_file

    def _get_date_range(self, ks_df_informations):
        """
        Get the appropriate date range based on the selected period type
        """
        company_id = ks_df_informations.get('company_id')
        company = self.env['res.company'].browse(company_id)

        # Get current date
        today = datetime.date.today()

        # Check if specific dates are provided
        date_info = ks_df_informations.get('date', {})

        if date_info.get('ks_start_date') and date_info.get('ks_end_date'):
            # Custom date range provided
            return {
                'start_date': date_info['ks_start_date'],
                'end_date': date_info['ks_end_date'],
                'period_name': 'Custom Date Range'
            }

        # Handle predefined periods based on ks_df_informations filter
        filter_type = ks_df_informations.get('ks_date_filter', 'this_month')

        if filter_type == 'today':
            return {
                'start_date': today.strftime('%Y-%m-%d'),
                'end_date': today.strftime('%Y-%m-%d'),
                'period_name': f'Today ({today.strftime("%d/%m/%Y")})'
            }

        elif filter_type == 'this_week':
            start_week = today - datetime.timedelta(days=today.weekday())
            end_week = start_week + datetime.timedelta(days=6)
            return {
                'start_date': start_week.strftime('%Y-%m-%d'),
                'end_date': end_week.strftime('%Y-%m-%d'),
                'period_name': f'This Week ({start_week.strftime("%d/%m/%Y")} to {end_week.strftime("%d/%m/%Y")})'
            }

        elif filter_type == 'this_month':
            start_month = today.replace(day=1)
            next_month = start_month.replace(
                month=start_month.month % 12 + 1) if start_month.month < 12 else start_month.replace(
                year=start_month.year + 1, month=1)
            end_month = next_month - datetime.timedelta(days=1)
            return {
                'start_date': start_month.strftime('%Y-%m-%d'),
                'end_date': end_month.strftime('%Y-%m-%d'),
                'period_name': f'This Month ({start_month.strftime("%B %Y")})'
            }

        elif filter_type == 'this_quarter':
            quarter = (today.month - 1) // 3 + 1
            start_quarter = today.replace(month=(quarter - 1) * 3 + 1, day=1)
            end_quarter_month = quarter * 3
            if end_quarter_month == 12:
                end_quarter = today.replace(month=12, day=31)
            else:
                end_quarter = today.replace(month=end_quarter_month + 1, day=1) - datetime.timedelta(days=1)
            return {
                'start_date': start_quarter.strftime('%Y-%m-%d'),
                'end_date': end_quarter.strftime('%Y-%m-%d'),
                'period_name': f'This Quarter (Q{quarter} {today.year})'
            }

        elif filter_type == 'this_financial_year':
            # Indian Financial Year: April 1 to March 31
            if today.month >= 4:
                fy_start = datetime.date(today.year, 4, 1)
                fy_end = datetime.date(today.year + 1, 3, 31)
                fy_year = f"{today.year}-{str(today.year + 1)[2:]}"
            else:
                fy_start = datetime.date(today.year - 1, 4, 1)
                fy_end = datetime.date(today.year, 3, 31)
                fy_year = f"{today.year - 1}-{str(today.year)[2:]}"

            return {
                'start_date': fy_start.strftime('%Y-%m-%d'),
                'end_date': fy_end.strftime('%Y-%m-%d'),
                'period_name': f'Current Financial Year (FY {fy_year})'
            }

        elif filter_type == 'last_financial_year':
            # Previous Financial Year
            if today.month >= 4:
                fy_start = datetime.date(today.year - 1, 4, 1)
                fy_end = datetime.date(today.year, 3, 31)
                fy_year = f"{today.year - 1}-{str(today.year)[2:]}"
            else:
                fy_start = datetime.date(today.year - 2, 4, 1)
                fy_end = datetime.date(today.year - 1, 3, 31)
                fy_year = f"{today.year - 2}-{str(today.year - 1)[2:]}"

            return {
                'start_date': fy_start.strftime('%Y-%m-%d'),
                'end_date': fy_end.strftime('%Y-%m-%d'),
                'period_name': f'Last Financial Year (FY {fy_year})'
            }

        elif filter_type == 'last_month':
            if today.month == 1:
                last_month_start = datetime.date(today.year - 1, 12, 1)
                last_month_end = datetime.date(today.year - 1, 12, 31)
            else:
                last_month_start = datetime.date(today.year, today.month - 1, 1)
                next_month = last_month_start.replace(
                    month=last_month_start.month % 12 + 1) if last_month_start.month < 12 else last_month_start.replace(
                    year=last_month_start.year + 1, month=1)
                last_month_end = next_month - datetime.timedelta(days=1)

            return {
                'start_date': last_month_start.strftime('%Y-%m-%d'),
                'end_date': last_month_end.strftime('%Y-%m-%d'),
                'period_name': f'Last Month ({last_month_start.strftime("%B %Y")})'
            }

        elif filter_type == 'last_quarter':
            current_quarter = (today.month - 1) // 3 + 1
            if current_quarter == 1:
                last_quarter = 4
                last_quarter_year = today.year - 1
            else:
                last_quarter = current_quarter - 1
                last_quarter_year = today.year

            start_quarter = datetime.date(last_quarter_year, (last_quarter - 1) * 3 + 1, 1)
            end_quarter_month = last_quarter * 3
            if end_quarter_month == 12:
                end_quarter = datetime.date(last_quarter_year, 12, 31)
            else:
                end_quarter = datetime.date(last_quarter_year, end_quarter_month + 1, 1) - datetime.timedelta(days=1)

            return {
                'start_date': start_quarter.strftime('%Y-%m-%d'),
                'end_date': end_quarter.strftime('%Y-%m-%d'),
                'period_name': f'Last Quarter (Q{last_quarter} {last_quarter_year})'
            }

        elif filter_type == 'last_year':
            last_year = today.year - 1
            return {
                'start_date': f'{last_year}-01-01',
                'end_date': f'{last_year}-12-31',
                'period_name': f'Last Year ({last_year})'
            }

        # Default to this month if no valid filter found
        else:
            start_month = today.replace(day=1)
            next_month = start_month.replace(
                month=start_month.month % 12 + 1) if start_month.month < 12 else start_month.replace(
                year=start_month.year + 1, month=1)
            end_month = next_month - datetime.timedelta(days=1)
            return {
                'start_date': start_month.strftime('%Y-%m-%d'),
                'end_date': end_month.strftime('%Y-%m-%d'),
                'period_name': f'This Month ({start_month.strftime("%B %Y")})'
            }

    def _build_complete_trial_balance_with_enhanced_groups(self, company_id, start_date, end_date):
        """
        Build complete trial balance data for grouping analysis with actual financial data
        """
        move_lines = {}

        # Get all accounts for the company
        all_accounts = self.env['account.account'].search([
            ('company_id', '=', company_id),
            ('deprecated', '=', False)
        ])

        # Initialize all accounts
        for account in all_accounts:
            move_lines[account.id] = {
                'name': account.name,
                'code': account.code,
                'account_id': account.id,
                'initial_debit': 0.0,
                'initial_credit': 0.0,
                'debit': 0.0,
                'credit': 0.0,
                'ending_debit': 0.0,
                'ending_credit': 0.0,
            }

        # Get initial balances (before start_date)
        initial_domain = [
            ('account_id', 'in', all_accounts.ids),
            ('date', '<', start_date),
            ('company_id', '=', company_id),
            ('move_id.state', '=', 'posted')
        ]

        initial_move_lines = self.env['account.move.line'].search(initial_domain)

        # Calculate initial balances
        for line in initial_move_lines:
            account_id = line.account_id.id
            if account_id in move_lines:
                move_lines[account_id]['initial_debit'] += line.debit
                move_lines[account_id]['initial_credit'] += line.credit

        # Get account move lines for the specified period
        domain = [
            ('account_id', 'in', all_accounts.ids),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
            ('company_id', '=', company_id),
            ('move_id.state', '=', 'posted')
        ]

        account_move_lines = self.env['account.move.line'].search(domain)

        # Calculate period balances
        for line in account_move_lines:
            account_id = line.account_id.id
            if account_id in move_lines:
                move_lines[account_id]['debit'] += line.debit
                move_lines[account_id]['credit'] += line.credit

        # Calculate ending balances for each account
        for account_id, line_data in move_lines.items():
            # Total debits and credits
            total_debit = line_data['initial_debit'] + line_data['debit']
            total_credit = line_data['initial_credit'] + line_data['credit']

            # Calculate net balance
            net_balance = total_debit - total_credit

            if net_balance > 0:
                line_data['ending_debit'] = net_balance
                line_data['ending_credit'] = 0.0
            else:
                line_data['ending_debit'] = 0.0
                line_data['ending_credit'] = abs(net_balance)

        return move_lines
