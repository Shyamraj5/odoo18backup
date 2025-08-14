import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { rpc } from "@web/core/network/rpc";

patch(PosOrderline.prototype, {
    setup(vals) {
        this.arabicName = this.product_id.arabic_name || "";
        return super.setup(...arguments);
    },
    getDisplayData() {
        return {
            ...super.getDisplayData(),
            arabicName: this.get_product().arabic_name || "",
        };
    },
});

patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            ...Orderline.props.line,
            shape: {
                ...Orderline.props.line.shape,
                arabicName: { type: String, optional: true },
            },
        },
    },
});
