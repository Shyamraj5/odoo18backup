import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { changesToOrder } from "@point_of_sale/app/models/utils/order_change";

patch(PosStore.prototype, {
    // @Override
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        if (order.pos_order_type_id){
            result.pos_order_type_id = order.pos_order_type_id;
            result.posOrderType = order.getPosOrderType() || '';
        }
        else{
            result.pos_order_type_id = null;
            result.posOrderType = '';
        }
        result.customerType = order.customer_type;
        result.posOrderType = order.pos_order_type_text;
        return result;
    },
});
