import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { rpc } from "@web/core/network/rpc";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate) {
        const self = this;
        var cashier = this.pos.get_cashier()
        const discountData = await rpc("/pos/discount_data",{
            data: cashier.id,
        });
        if (self.pos.config.enable_discount_validation && cashier._role != 'manager') {
            self.pos.refresh_validate_order = true;
            var orderlines = this.currentOrder.get_orderlines()
            var flag = 1;
            var employee_discount = discountData.discount_limit || 0
            var config_discount_limit = self.pos.config.discount_limit || 0; // Default to 0 if not set
            var discountLimit = employee_discount > 0 ? employee_discount : config_discount_limit;
            orderlines.forEach((order) => {
                if(order.discount > discountLimit)
                flag = 0;
            });
            if (flag != 1) {
                this.dialog.add(NumberPopup, {
                    title: _t('Enter Validation PIN'),
                    startingValue: '',
                    formatDisplayedValue: (x) => x.replace(/./g, "•"), // Hide PIN digits
                    getPayload: async (enteredPin) => {
                        const validPin = discountData.manager_pin;
                        if (enteredPin === validPin) {
                            // PIN is correct, proceed with validation
                            self.pos.get_order().validate_check = false;
                            return super.validateOrder(isForceValidate);
                        } else {
                            // Wrong PIN, show error popup
                            await this.dialog.add(AlertDialog, {
                                title: _t('Invalid PIN'),
                                body: _t('The entered PIN is incorrect. Please try again.'),
                            });
                            // Don't proceed with validation
                            return;
                        }
                    },
                });
            } else {
                self.pos.get_order().validate_check = false;
                return super.validateOrder(isForceValidate);
            }
        }
        else {
            self.pos.get_order().validate_check = false;
                return super.validateOrder(isForceValidate);
            }
    },

    
});



