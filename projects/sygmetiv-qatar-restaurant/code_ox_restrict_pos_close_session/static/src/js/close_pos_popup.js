/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { rpc } from "@web/core/network/rpc";

patch(ClosePosPopup.prototype, {
    async confirm() {
        const self = this;
        var cashier = self.pos.get_cashier()
        const order = self.pos.get_order();
        const employeeData = await rpc("/pos/discount_data",{
            data: cashier.id,
        });

        if (this.pos.config.enable_closure_validation && cashier._role != 'manager') {
            self.pos.refresh_close_check = true;
            this.dialog.add(NumberPopup, {
                title: _t("Manager PIN Required"),
                formatDisplayedValue: (x) => x.replace(/./g, "•"),
                getPayload: async (enteredPin) => {
                    const validPin = employeeData.manager_pin;
                    if (enteredPin === validPin) {
                        // PIN is correct, proceed with closing session
                        super.confirm();
                    } else {
                        // Wrong PIN, show error popup
                        await this.dialog.add(AlertDialog, {
                            title: _t('Invalid PIN'),
                            body: _t('The entered PIN is incorrect. Please try again.'),
                        });
                        // Don't close session
                        return;
                    }
                },
            });
        }
        else {
            super.confirm();
        }
    },
});