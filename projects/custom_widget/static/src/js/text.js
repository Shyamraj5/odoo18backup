/** @odoo-module **/
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, xml } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class MyTextField extends Component {
   static template = xml`
      <input t-att-id="props.id" class="text-danger" t-att-value="props.value" onChange.bind="onChange" />
   `;
   static props = { ...standardFieldProps };
   static supportedTypes = ["char"];

   /**
   * @param {boolean} newValue
   */
   onChange(newValue) {
      this.props.update(newValue);
   }
}

registry.category("fields").add("my_text_field", MyTextField);
