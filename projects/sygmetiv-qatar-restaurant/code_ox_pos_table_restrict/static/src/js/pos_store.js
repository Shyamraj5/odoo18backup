import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { changesToOrder } from "@point_of_sale/app/models/utils/order_change";
import { rpc } from "@web/core/network/rpc";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    // @Override
    async pay() {
        const currentOrder = this.get_order();
        if (currentOrder.user_id?.id != this.user.id){
            await this.dialog.add(AlertDialog, {
                title: _t('Access Denied'),
                body: _t('This order is already being handled by another user.'),
            });
            return
        }
        return super.pay(...arguments);
    }
});
