/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class IntegerStepperWidget extends Component {
    static props = {
        ...standardFieldProps,
        update: { type: Function, optional: true },
    };
    

    setup() {
        this.state = useState({ value: this.props.value || 0 });
    }

    increment() {
        this.state.value += 1;
        if (this.props.update) {
            this.props.update(this.state.value);
        }
    }
    
    decrement() {
        this.state.value -= 1;
        if (this.props.update) {
            this.props.update(this.state.value);
        }
    }
    
    
    
}
IntegerStepperWidget.template = "custom_widget.IntegerStepperWidget";

export const integerstepperwidget = {
    component: IntegerStepperWidget,
};

registry.category("fields").add("integer_stepper", integerstepperwidget);
