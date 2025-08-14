/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        
        this.customer_type = vals.customer_type || 'walk_in_customer';
        if(this.config.default_order_type_id && !this.pos_order_type_id && !this.uiState.locked){
            this.update({ pos_order_type_id: this.config.default_order_type_id });
        }

        if (typeof vals.pos_order_type_id === "number"){
            this.pos_order_type_id = vals.pos_order_type_id;
            this.pos_order_type_text = vals.pos_order_type_text
        }
        else if (vals.pos_order_type_id){
            this.pos_order_type_id = vals.pos_order_type_id;
            this.pos_order_type_text = vals.pos_order_type_id.name;
        }
        
    },
    set_customer_type(customer_type) {
        this.update({ customer_type: customer_type });
    },

    getPosOrderType() {
        const data = this.models['pos.order.type'].find(type => type.id === this.pos_order_type_id);
        if (data){
            return data.name
        }
        else{
            return ''
        }
    },

    set_pos_order_type(pos_order_type_id) {
        this.update({ 
            pos_order_type_id: pos_order_type_id.id,
            pos_order_type_text: pos_order_type_id.name
        });
    },

    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        return {
            ...result,
            pos_order_type_id: this.pos_order_type_id,
            customerType: this.customer_type,
            pos_order_type_text: this.pos_order_type_text || ""
        };
    },
});
