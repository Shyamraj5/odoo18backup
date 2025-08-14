/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class OrderTypeDialog extends Component {
    setup() {
        this.state = useState({
            options: this.props.options || [],
            selectedOption: this.props.selectedValue || null,
        });
    }

    updateSelection = (optionId) =>{
        this.state.selectedOption = parseInt(optionId, 10) || 0;
        this.confirm();
        console.log(this.state.selectedOption);
    }

    confirm() {
        if (this.props.onConfirm) {
            this.props.onConfirm(this.state.selectedOption);
        }
        this.props.close();
    }

    cancel() {
        if (this.props.onCancel) {
            this.props.onCancel();
        }
        this.props.close();
    }
}

OrderTypeDialog.template = "codeox_pos_order_types.OrderTypeDialog";
OrderTypeDialog.components = { Dialog };
