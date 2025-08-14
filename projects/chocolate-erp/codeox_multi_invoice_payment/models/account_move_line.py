from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _prepare_reconciliation_single_partial(
        self,
        debit_values,
        credit_values,
        shadowed_aml_values=None,
    ):
        am_model = self.env["account.move"]
        aml_model = self.env["account.move.line"]
        partials = super(AccountMoveLine, self)._prepare_reconciliation_single_partial(
            debit_values,
            credit_values,
            shadowed_aml_values=shadowed_aml_values,
        )
        if self.env.context.get("paid_amount", 0.0):
            total_paid = self.env.context.get("paid_amount", 0.0)
            current_am = am_model.browse(self.env.context.get("move_id"))
            current_aml = aml_model.browse(self.env.context.get("line_id"))
            # decimal_places = current_am.company_id.currency_id.decimal_places
            if current_am.currency_id.id != current_am.company_currency_id.id:
                total_paid = current_am.currency_id._convert(
                    total_paid,
                    current_aml.currency_id,
                    current_am.company_id,
                    current_aml.date,
                )

            partial = partials.get("partial_values")
            debit_values = partials.get("debit_values")
            credit_values = partials.get("credit_values")

            debit_line = self.browse(partial.get("debit_move_id"))
            credit_line = self.browse(partial.get("credit_move_id"))
            different_currency = debit_line.currency_id.id != credit_line.currency_id.id
            to_apply = min(total_paid, partial.get("amount", 0.0))
            existing_amount = partial.get("amount", 0.0)
            partial.update(
                {
                    "amount": to_apply,
                }
            )

            # TODO: maybe pass these two if condition to else condition if different
            # currency
            if debit_values:
                debit_values.update(
                    {
                        "amount_residual": debit_values.get("amount_residual", 0.0)
                        + existing_amount
                        - to_apply,
                    }
                )
            if credit_values:
                credit_values.update(
                    {
                        "amount_residual": credit_values.get("amount_residual", 0.0)
                        + existing_amount
                        - to_apply,
                    }
                )

            if different_currency:
                # TODO: work on this
                partial.update(
                    {
                        "debit_amount_currency": credit_line.company_currency_id._convert(  # noqa
                            to_apply,
                            debit_line.currency_id,
                            credit_line.company_id,
                            credit_line.date,
                        ),
                        "credit_amount_currency": debit_line.company_currency_id._convert(  # noqa
                            to_apply,
                            credit_line.currency_id,
                            debit_line.company_id,
                            debit_line.date,
                        ),
                    }
                )
            else:
                partial.update(
                    {
                        "debit_amount_currency": to_apply,
                        "credit_amount_currency": to_apply,
                    }
                )
        return partials
