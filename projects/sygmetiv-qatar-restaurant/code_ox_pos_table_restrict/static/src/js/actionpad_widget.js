import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
/**
 * @props partner
 */

patch(ActionpadWidget.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
    },

    async submitOrder() {
        const order = this.pos.get_order();
        if (this.pos.user.id != order.user_id.id){
            await this.dialog.add(AlertDialog, {
                title: _t('Access Denied'),
                body: _t('This table is already being handled by another user.'),
            });
            return
        }
        if (!this.uiState.clicked) {
            this.uiState.clicked = true;
            try {
                await this.pos.sendOrderInPreparationUpdateLastChange(this.currentOrder);
            } finally {
                this.uiState.clicked = false;
            }
        }
    },
});
