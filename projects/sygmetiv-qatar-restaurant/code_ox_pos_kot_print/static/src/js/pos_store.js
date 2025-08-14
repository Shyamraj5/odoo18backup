import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { changesToOrder } from "@point_of_sale/app/models/utils/order_change";
const { DateTime } = luxon;

patch(PosStore.prototype, {
    // @Override
    async printReceipts(order, printer, title, lines, fullReceipt = false, diningModeUpdate) {
        const receipt = await this.getRenderedReceipt(
            order,
            title,
            lines,
            fullReceipt,
            diningModeUpdate
        );
        const result = await printer.printReceipt(receipt, order.config_id.id);
        return result.successful;
    },

    getPrintingChanges(order, diningModeUpdate) {
        const time = DateTime.now().toFormat("HH:mm");
        return {
            table_name: order.table_id ? order.table_id.table_number : "",
            config_name: order.config.name,
            time: time,
            tracking_number: order.tracking_number,
            takeaway: order.config.takeaway && order.takeaway,
            employee_name: order.employee_id?.name || order.user_id?.name,
            order_note: order.general_note,
            diningModeUpdate: diningModeUpdate,
            order_type: order.pos_order_type_text
        };
    }
});
