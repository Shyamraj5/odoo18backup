
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { rpc } from "@web/core/network/rpc";

patch(ControlButtons.prototype, {
    async clickDiscount() {
        const self = this;
        var cashier = self.pos.get_cashier()
        const discountData = await rpc("/pos/discount_data",{
            data: cashier.id,
        });
        this.dialog.add(NumberPopup, {
            title: _t("Discount Percentage"),
            startingValue: this.pos.config.discount_pc,
            getPayload: (num) => {
                const val = Math.max(
                    0,
                    Math.min(100, this.env.utils.parseValidFloat(num.toString()))
                );
                var employee_discount = discountData.discount_limit ? discountData.discount_limit : 0
                var config_discount_limit = self.pos.config.discount_limit || 0
                var discountLimit = employee_discount > 0 ? employee_discount : config_discount_limit;
                if (this.pos.config.enable_discount_validation && val > discountLimit && cashier._role != 'manager') {
                    this.pos.refresh_discount_check = true;

                    this.dialog.add(NumberPopup, {
                        title: _t("Manager PIN Required"),
                        formatDisplayedValue: (x) => x.replace(/./g, "•"),
                        getPayload: async (enteredPin) => {
                            const validPin = discountData.manager_pin;
                            if (enteredPin === validPin) {
                                // PIN is correct, proceed with discount
                                this.pos.get_order().discount_check = false;
                                this.apply_discount(val);
                            } else {
                                // Wrong PIN, show error popup
                                await this.dialog.add(AlertDialog, {
                                    title: _t('Invalid PIN'),
                                    body: _t('The entered PIN is incorrect. Please try again.'),
                                });
                                // Don't apply the discount
                                return;
                            }
                        },
                    });
                } else {
                    // Discount is 30% or less, apply directly
                    this.apply_discount(val);
                }
            },
        });
    },
});