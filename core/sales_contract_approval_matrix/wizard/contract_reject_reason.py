from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SalesContractRejectWizard(models.TransientModel):
    _name = "account.analytic.account.contract.reject.wizard"
    _description = "Wizard for Sales Contract Reject Reason"

    name = fields.Text(string="Reason", required=1)

    @api.multi
    def wizard_contract_reject_reason(self):
        contract_obj = self.env['account.analytic.account']
        contracts = contract_obj.browse(self._context.get('active_ids', []))

        email_to_manager = False

        for contract in contracts:
            reason = self.name

            email_to_manager = contract_obj.sudo().send_rejection_email_to_manager(contract, reason)
            contract.write({'state': 'rejected'})

            if email_to_manager:
                user = self.env['res.users'].sudo().search([('id', '=', int(self._uid))])
                if user:
                    msg = _("<p><ul><li>Contract Rejected by: %s</li><li>Contract Type: %s</li></ul></p>") % (str(user.name), str(contract.contract_type_id.name))
                    contract.sudo().message_post(body=msg)

        return True