/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { CustomerTypeDialog } from "./customer_type_dialog";
import { OrderTypeDialog } from "./order_type_dialog";
import { useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialogService = useService("dialog");
        this.state = useState({
            customerType: false,
            options: [
                { name: "Outside", value: "walk_in_customer" },
                { name: "Room Guest", value: "hotel_customer" },
                { name: "Complementary", value: "complementary_customer" }
            ]
        });

        this.rpc = rpc;

        let currentOrder = this.pos.get_order();
        if (currentOrder) {
            let selectedCustomerType = this.state.options.find(
                (customerType) => customerType.value === this.currentOrder.customer_type
            );
            this.state.customerType = selectedCustomerType || false;
            this.state.orderType = this.currentOrder.pos_order_type_id || false;
        }
    },

    openDialog() {
        let currentOrder = this.pos.get_order();
        if (!currentOrder) return;

        let selectedCustomerType = this.state.options.find(
            (customerType) => customerType.value === currentOrder.customer_type
        );
        this.state.customerType = selectedCustomerType || null;
        this.dialogService.add(CustomerTypeDialog, {
            title: _t("Select Customer Type"),
            options: this.state.options,
            selectedValue: selectedCustomerType ? selectedCustomerType.value : null,
            onConfirm: (selectedValue) => {
                if (selectedValue && selectedValue !== this.currentOrder.customer_type) {
                    this.currentOrder.customer_type = selectedValue;
                    this.state.customerType = this.state.options.find(
                        (customerType) => customerType.value === selectedValue
                    ) || null;
                }
            },
            onCancel: () => console.log("Dialog cancelled!"),
        });
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
        }
    },
});
