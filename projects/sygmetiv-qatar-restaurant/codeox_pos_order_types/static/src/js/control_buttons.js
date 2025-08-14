/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { OrderTypeDialog } from "./order_type_dialog";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

patch(ControlButtons.prototype, {
    async setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
        this.state = useState({
            orderTypeName: ''
        });        
        this.rpc = rpc;
        this.state.orderTypeOptions = await this.getPosOrderTypes();
        const selectedOrderType = this.state.orderTypeOptions.find(
            (type) => type.id === this.pos.config.default_order_type_id.id
        );
        this.state.orderTypeName = selectedOrderType.name;

        let currentOrder = this.pos.get_order();
        if (currentOrder) {
            this.state.orderType = this.currentOrder.pos_order_type_id || false;
        }
    },

    async openOrderTypeDialog() {
        const currentOrder = this.pos.get_order();
        if (!currentOrder) return;
        
        this.state.orderTypeOptions = await this.getPosOrderTypes();
        if (!this.state.orderTypeOptions.length) {
            console.warn("No order types available.");
            return;
        }
        
        this.dialogService.add(OrderTypeDialog, {
            title: _t("Select Order Type"),
            options: this.state.orderTypeOptions,
            selectedValue: this.currentOrder.pos_order_type_id || false,
            onConfirm: (selectedValue) => this.updateOrderType(this.currentOrder, selectedValue),
            onCancel: () => console.log("Dialog cancelled!"),
        });
    },

    async getPosOrderTypes() {
        return await this.rpc("/pos/pos_order_type");
    },

    updateOrderType(currentOrder, selectedValue) {        
        const selectedOrderType = this.state.orderTypeOptions.find(
            (type) => type.id === selectedValue
        );
        if (selectedOrderType) {
            currentOrder.set_pos_order_type(selectedOrderType);
            currentOrder.posOrderTypeName = selectedOrderType.name;
            if (typeof currentOrder.id === "number") {
                this.pos.data.write("pos.order", [currentOrder.id], {
                    pos_order_type_id: selectedOrderType.id,
                    pos_order_type_text: selectedOrderType.name,
                });
            }
            this.state.orderType = selectedValue;
            this.state.orderTypeName = selectedOrderType.name;
        }
    },
});
