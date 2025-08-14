/** @odoo-module **/
const {Component} = owl;
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useService} from "@web/core/utils/hooks";

export class SalePurchaseHistoryWidget extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    viewProductHistory() {
        this.actionService.doAction(
            "product_transaction_history.sale_purchase_history_action",
            {
                additionalContext: {
                    default_product_id: this.props.record.data.product_id[0],
                    default_partner_id: this.props.record.data.order_partner_id[0],
                },
            }
        );
    }
}

SalePurchaseHistoryWidget.template = "product_transaction_history.product_history_widget";

export const salePurchaseHistoryWidget = {
    component: SalePurchaseHistoryWidget,
};

registry.category("view_widgets").add("sale_purchase_history_widget", salePurchaseHistoryWidget);
