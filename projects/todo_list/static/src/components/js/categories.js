import { registry } from "@web/core/registry";


import { useState, onWillStart, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TodoCategory extends Component {
    setup() {
        this.orm = useService("orm");
        this.categories = useState({ list: [] });

        onWillStart(async () => {
            this.categories.list = await this.orm.searchRead("todo.category", [], ["id", "name"]);
        });
    }
}
TodoCategory.template = "todo_list.TodoCategoryTemplate";
registry.category("actions").add("owl.action_categ_js", TodoCategory);
