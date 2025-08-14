/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CustomerTypeDialog extends Component {
    setup() {
        this.state = useState({
            options: this.props.options || [],
            selectedOption: this.props.selectedValue || null,
        });
    }

    updateSelection = (option) =>{
        this.state.selectedOption = option;
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

CustomerTypeDialog.template = "code_ox_pos_generic_customisation.CustomerTypeDialog";
CustomerTypeDialog.components = { Dialog };
