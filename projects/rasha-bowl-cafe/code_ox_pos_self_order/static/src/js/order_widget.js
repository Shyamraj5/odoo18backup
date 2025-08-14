/** @odoo-module **/
import { OrderWidget } from "@pos_self_order/app/components/order_widget/order_widget"
import { patch } from "@web/core/utils/patch";

patch(OrderWidget.prototype, {
    setup() {
        super.setup(...arguments);
    },
    
    showProductCategory() {
        this.selfOrder.showProductCategories = true;
        this.selfOrder.showProducts = false;
    }

});