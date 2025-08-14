import { patch } from "@web/core/utils/patch";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(OrderSummary.prototype, {
    async unbookTable() {
        const order = this.pos.get_order();
        if (this.pos.user.id != order.user_id.id){
            await this.dialog.add(AlertDialog, {
                title: _t('Access Denied'),
                body: _t('This table is already being handled by another user.'),
            });
            return
        }
        await this.pos.deleteOrders([order]);
        this.pos.showScreen(this.pos.firstScreen);
    },
});
